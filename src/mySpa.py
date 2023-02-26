""" Sample client demonstrating async use of GeckoLib """
# import configuration variables
import config

import const

import asyncio
import logging

from datetime import datetime

from geckolib import (GeckoSpaEvent, GeckoSpaState)
from geckolib import GeckoAsyncSpaMan

from geckolib import (GeckoWaterCare, GeckoReminders, GeckoStructAccessor)

from geckolib import GeckoConstants


logger = logging.getLogger(__name__)


class MySpa(GeckoAsyncSpaMan):
    """Spa man implementation"""

    global logger

    def __init__(self, client_uuid: str, **kwargs: str) -> None:
        super().__init__(client_uuid, **kwargs)

        self._onValueChange = None

    def onValueChange(self, callback) -> None:
        self._onValueChange = callback

    async def handle_event(self, event: GeckoSpaEvent, **kwargs) -> None:
        # Uncomment this line to see events generated
        # print(f"{event}: {kwargs}")

        if event == GeckoSpaEvent.CONNECTION_SPA_COMPLETE:
            logger.info("Connection to SPA is ready.")
            logger.info("Spa Name       : " + self._spa.descriptor.name)
            logger.info("Spa Version    : " + self._spa.version)
            logger.info("Spa Revision   : " + self._spa.revision)
            logger.info("Spa IP address : " + self._spa.descriptor.ipaddress)

        if event == GeckoSpaEvent.CLIENT_FACADE_IS_READY:

            logger.info("SPA facade is ready.")
            self._can_use_facade = True

            # at least publish once all values once
            await self._refreshAll()

            # add the watcher to see all changes
            self._facade.watch(OnChange(self))

            self.wait_for_descriptors

        elif event in (
            GeckoSpaEvent.CLIENT_FACADE_TEARDOWN,
            GeckoSpaState.ERROR_NEEDS_ATTENTION,
        ):
            self._can_use_facade = False

    ########################
    #
    # Refresh all values
    #
    ###################

    async def _refreshAll(self) -> None:
        self.refreshBlower()
        self.refreshFilters()
        self.refreshHeater()
        self.refreshLights()
        self.refreshPumps()
        self.refreshReminders()
        self.refreshWaterCare()
        self.refreshOzoneMode()
        self.refreshSmartWinterMode()

    ########################
    #
    # Refresh water care values only
    #
    ###################

    def refreshWaterCare(self) -> None:

        if self._onValueChange is None:
            logger.error("No OnValueChange callback defined")
        else:
            logger.debug("Refreshing water care data")

            # get's the values for water care module and create a nice json payload

            # get care mode
            mode = self._facade.water_care.mode
            if mode == None:  # only to ensure a real value
                mode = 1

            # get care modes
            modes = self._facade.water_care.modes
            # care mode as text
            mode_txt = modes[mode]

            # get actual time
            now = datetime.now()  # current date and time

            mode_len = len(modes) - 1

            json = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '",'
            json += f'"mode":{mode}, "modes":['

            for index, mode_text in enumerate(modes):
                json += "{"
                json += f'"text":"{mode_text}",'
                json += f'"value":{index}}},'

            json = json[:-1]  # remove last comma
            json += f'], "mode(txt)":"{mode_txt}"'
            json += '}'

            self._onValueChange(const.TOPIC_WATERCARE, json)

    ########################
    #
    # Refresh blower values only
    #
    ###################

    def refreshBlower(self) -> None:

        if self._onValueChange is None:
            logger.error("No OnValueChange callback defined")
        else:
            logger.debug("Refreshing blowers data")
            # get actual time
            now = datetime.now()  # current date and time

            json = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '"'
            for blower in self._facade.blowers:
                json += f',"{blower.name}":"{blower.state_sensor().state}"'
            json += '}'

            self._onValueChange(const.TOPIC_BLOWERS, json)

    ########################
    #
    # Refresh pump values only
    #
    ###################

    def refreshPumps(self) -> None:

        if self._onValueChange is None:
            logger.error("No OnValueChange callback defined")
        else:
            logger.debug("Refreshing pumps data")

            # get actual time
            now = datetime.now()  # current date and time

            # loop over all pumps
            json = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '"'
            for pump in self._facade.pumps:
                json += f',"{pump.name}":"{pump.mode}"'

            # find circulation pump
            for sensor in self._facade.binary_sensors:
                if sensor.key == "CIRCULATING PUMP":
                    json += f',"{sensor.name}":"{sensor.state}"'
                    break
            json += '}'

            self._onValueChange(const.TOPIC_PUMPS, json)

    ########################
    #
    # Refresh light values only
    #
    ###################
    def refreshLights(self) -> None:

        if self._onValueChange is None:
            logger.error("No OnValueChange callback defined")
        else:
            logger.debug("Refreshing lights data")
            # get actual time
            now = datetime.now()  # current date and time

            json = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '"'
            for light in self._facade.lights:
                json += f',"{light.name}":"{light.state_sensor().state}"'
            json += '}'

            self._onValueChange(const.TOPIC_LIGHTS, json)

    ########################
    #
    # Refresh heater values only
    #
    ###################
    def refreshHeater(self) -> None:

        if self._onValueChange is None:
            logger.error("No OnValueChange callback defined")
        else:
            logger.debug("Refreshing heater data")

            # get actual time
            now = datetime.now()  # current date and time

            json = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '",'
            json += f'"current_operation": "{self._facade.water_heater.current_operation}",'
            json += f'"temperature_unit":"{self._facade.water_heater.temperature_unit}",'
            json += f'"current_temperature":{self._facade.water_heater.current_temperature},'
            json += f'"target_temperature":{self._facade.water_heater.target_temperature},'
            json += f'"real_target_temperature":{self._facade.water_heater.real_target_temperature}'
            json += '}'

            self._onValueChange(const.TOPIC_WATERHEAT, json)

    ########################
    #
    # Refresh reminders values only
    #
    ###################
    def refreshReminders(self) -> None:

        if self._onValueChange is None:
            logger.error("No OnValueChange callback defined")
        else:
            logger.debug("Refreshing reminder data")

            '''
            get's the active remainders and create a nice json payload
            '''
            reminders = self._facade.reminders_manager.reminders
            if (reminders is None) or (len(reminders) == 0):
                logger.debug('No reminders received')
                return

            reminders_len = len(reminders) - 1

            # get actual time
            now = datetime.now()  # current date and time

            json = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '",'
            #json += '{'
            i = 0
            for reminder in reminders:
                json += f'"{reminder.description}":"{reminder.days}"'
                if (i < reminders_len):
                    json += ","
                i += 1
            json += '}'

            if json is not None:
                self._onValueChange(const.TOPIC_REMINDERS, json)

    ########################
    #
    # Refresh filter values only
    #
    ###################

    def refreshFilters(self) -> None:

        if self._onValueChange is None:
            logger.error("No OnValueChange callback defined")
        else:

            logger.debug("Refreshing filter data")
            for sensor in self._facade.binary_sensors:
                if (sensor.name == 'Filter Status:Clean'):
                    filerStatusClean = sensor.state
                if (sensor.name == 'Filter Status:Purge'):
                    filerStatusPurge = sensor.state

            # get actual time
            now = datetime.now()  # current date and time
            json = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '",'
            json += f'"Filter Status:Clean":"{str(filerStatusClean).lower()}",'
            json += f'"Filter Status:Purge":"{str(filerStatusPurge).lower()}"'
            json += '}'

            self._onValueChange(const.TOPIC_FILTER_STATUS, json)

    ########################
    #
    # Refresh Smart Winter mode values only
    #
    ###################
    def refreshSmartWinterMode(self) -> None:
        if self._onValueChange is None:
            logger.error("No OnValueChange callback defined")
        else:

            logger.debug("Refreshing filter data")
            for sensor in self._facade.binary_sensors:
                if (sensor.name == 'Smart Winter Mode:Active'):
                    swmActive = sensor.state
            for sensor in self._facade.sensors:
                if (sensor.name == 'Smart Winter Mode:Risk'):
                    swmRisk = sensor.state

            # get actual time
            now = datetime.now()  # current date and time
            json = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '",'
            json += f'"Smart Winter Mode:Active":"{str(swmActive).lower()}",'
            json += f'"Smart Winter Mode:Risk":"{str(swmRisk).lower()}"'
            json += '}'

            self._onValueChange(const.TOPIC_SMARTWINTERMODE, json)

    ########################
    #
    # Refresh Ozone/BromiCharge values only
    #
    ###################
    def refreshOzoneMode(self) -> None:
        if self._onValueChange is None:
            logger.error("No OnValueChange callback defined")
        else:

            logger.debug("Refreshing filter data")
            for sensor in self._facade.binary_sensors:
                if (sensor.name == 'Ozone'):
                    ozoneMode = sensor.state

            # get actual time
            now = datetime.now()  # current date and time
            json = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '",'
            json += f'"Ozone Mode":"{str(ozoneMode).lower()}"'
            json += '}'

            self._onValueChange(const.TOPIC_OZONEMODE, json)

    ################
    #
    # Switch the pump #  ON/OFF
    #
    ##############

    async def set_pumps(self, client, userdata, message):
        '''
        Switch pump state
        '''
        topic = str(message.topic)
        msg = str(message.payload.decode("UTF-8"))
        logger.debug(f'msg received: topic: {topic}, payload: {msg}')
        if (msg.startswith("set_pump")):
            # get pump
            values = msg.split(":")
            if len(values) != 2:
                logger.warn("Wrong payload of setting pumps received.")
                return
            parts = values[1].split("=")
            if len(parts) != 2:
                logger.warn("Wrong payload of setting pumps received.")
                return
            # payload seems to be OK --> proceed
            try:
                pump = int(parts[0])
            except Exception as ex:
                logger.warn(f"Pump number conversion error: {ex.args}")
                return
            if pump < 0 or pump > len(self._facade.pumps):
                logger.warn(f"Pump number {pump} does not exist.")
                return

            if "HI" == parts[1]:
                logger.info(f"Switching pump {pump} on")
                await self._facade.pumps[pump].async_set_mode("HI")
            elif "OFF" == parts[1]:
                logger.info(f"Switching pump {pump}  off")
                await self._facade.pumps[pump].async_set_mode("OFF")

    ################
    #
    # Switch the first light ON/OFF
    #
    ##############

    async def set_lights(self, client, userdata, message):
        '''
        Switch light state
        '''
        topic = str(message.topic)
        msg = str(message.payload.decode("UTF-8"))
        logger.debug(f'msg received: topic: {topic}, payload: {msg}')
        if (msg.startswith("set_lights")) and self.facade.lights[0] is not None:
            parts = msg.split("=")
            if len(parts) == 2:
                if "HI" == parts[1]:
                    logger.info("Switching lights on")
                    await self._facade.lights[0].async_turn_on()
                    logger.info("Light switched on")
                elif "OFF" == parts[1]:
                    logger.info("Switching lights off")
                    await self._facade.lights[0].async_turn_off()

    ################
    #
    # Switch the first blower ON/OFF
    #
    ##############

    async def set_blowers(self, client, userdata, message):
        '''
        Switch blower state
        '''
        topic = str(message.topic)
        msg = str(message.payload.decode("UTF-8"))
        logger.debug(f'msg received: topic: {topic}, payload: {msg}')
        if (msg.startswith("set_blower")) and self.facade.blowers[0] is not None:
            parts = msg.split("=")
            if len(parts) == 2:
                if "HI" == parts[1]:
                    logger.info("Switching blower on")
                    await self._facade.blowers[0].async_turn_on()
                    logger.info("Blower switched on")
                elif "OFF" == parts[1]:
                    logger.info("Switching blower off")
                    await self._facade.blowers[0].async_turn_off()

    ################
    #
    # Sets the the water care mode
    #
    ##############

    async def set_watercare(self, client, userdata, message):
        '''
        Set water care mode
        '''
        topic = str(message.topic)
        msg = str(message.payload.decode("UTF-8"))
        logger.debug(f'msg received: topic: {topic}, payload: {msg}')
        if (msg.startswith("set_watercare")):
            parts = msg.split("=")
            if len(parts) == 2:
                try:
                    mode = int(parts[1])
                except:
                    logger.error(f"Wrong mode received: {parts[1]}")
                    return
                await self._facade.water_care.async_set_mode(mode)

    ################
    #
    # Sets the the temperature
    #
    ##############
    async def set_temperature(self, client, userdata, message):
        '''
        Set the new target temperature
        '''
        topic = str(message.topic)
        msg = str(message.payload.decode("UTF-8"))
        logger.debug(f'msg received: topic: {topic}, payload: {msg}')
        if (msg.startswith("set_temp")):
            parts = msg.split("=")
            if len(parts) == 2:
                try:
                    temp = float(parts[1])
                    if temp < 15 and temp > 40:
                        logger.warn(
                            f"Temperature {temp} outside allowed values")
                        return
                    await self.facade.water_heater.async_set_target_temperature(temp)
                    logger.info(f"Target temperature set to {temp}")
                except:
                    logger.error(
                        f"Wrong temperature value received: {parts[1]}")
                    return

    ################
    #
    # Refresh all MQTT values
    #
    ##############
    async def refresh_all(self, client, userdata, message):
        '''
        Set the new target temperature
        '''
        topic = str(message.topic)
        msg = str(message.payload.decode("UTF-8"))
        logger.debug(f'msg received: topic: {topic}, payload: {msg}')
        if (msg == "refresh_all"):
            await self._refreshAll()


class OnChange():
    def __init__(self, mySpa: MySpa) -> None:
        self._mySpa = mySpa

    def __call__(self, sender, old_value, new_value):
        logger.debug(
            f"on_spa_change: >{sender}< changed from {old_value} to {new_value}")
        print(f">{sender}< changed from {old_value} to {new_value}")

        # only if facade is ready
        if not self._mySpa._can_use_facade:
            return

        if isinstance(sender, GeckoReminders):
            self._mySpa.refreshReminders()

        elif isinstance(sender, GeckoWaterCare):
            self._mySpa.refreshWaterCare()

        elif isinstance(sender, GeckoStructAccessor):
            if sender.tag == "UdLi":
                self._mySpa.refreshLights()

            elif sender.tag == "CP" or sender.tag == "P1" or sender.tag == "P2" or sender.tag == "P3":
                self._mySpa.refreshPumps()

            elif sender.tag == "SetpointG" or sender.tag == "RealSetPointG" or sender.tag == "DisplayedTempG" or sender.tag == "Heating":
                self._mySpa.refreshHeater()

            elif sender.tag == "BL":
                self._mySpa.refreshBlower()

            elif sender.tag == "SwmRisk" or sender.tag == "SwmActive":
                self._mySpa.refreshSmartWinterMode()

            elif sender.tag == "O3":
                self._mySpa.refreshOzoneMode()

            elif sender.tag == "Clean" or sender.tag == "Purge":
                self._mySpa.refreshFilters()

            else:
                logger.warn(
                    f"Not handled GeckoStructAccessor sender tag received: {sender.tag}")
                logger.warn(
                    f"  --> {sender} changed from {old_value} to {new_value}")

        else:
            logger.warn(
                f"Change not check. Sender: {sender}, sender-type: {sender.type()}")
