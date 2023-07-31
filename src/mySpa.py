""" Sample client demonstrating async use of GeckoLib """
# import configuration variables
import config
import const

import asyncio
import json
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

            # get the values for water care module and create a nice json payload

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

            cjson = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '",'
            cjson += f'"mode":{mode}, "modes":['

            for index, mode_text in enumerate(modes):
                cjson += "{"
                cjson += f'"text":"{mode_text}",'
                cjson += f'"value":{index}}},'

            cjson = cjson[:-1]  # remove last comma
            cjson += f'], "mode(txt)":"{mode_txt}"'
            cjson += '}'

            self._onValueChange(const.TOPIC_WATERCARE, cjson)

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

            cjson = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '"'
            for blower in self._facade.blowers:
                cjson += f',"{blower.name}":"{blower.state_sensor().state}"'
            cjson += '}'

            self._onValueChange(const.TOPIC_BLOWERS, cjson)

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
            cjson = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '"'
            for pump in self._facade.pumps:
                cjson += f',"{pump.name}":"{pump.mode}"'

            # find circulation pump
            for sensor in self._facade.binary_sensors:
                if sensor.key == "CIRCULATING PUMP":
                    cjson += f',"{sensor.name}":"{sensor.state}"'
                    break
            cjson += '}'

            self._onValueChange(const.TOPIC_PUMPS, cjson)

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

            cjson = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '"'
            for light in self._facade.lights:
                cjson += f',"{light.name}":"{light.state_sensor().state}"'
            cjson += '}'

            self._onValueChange(const.TOPIC_LIGHTS, cjson)

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

            cjson = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '",'
            cjson += f'"current_operation": "{self._facade.water_heater.current_operation}",'
            cjson += f'"temperature_unit":"{self._facade.water_heater.temperature_unit}",'
            cjson += f'"current_temperature":{self._facade.water_heater.current_temperature},'
            cjson += f'"target_temperature":{self._facade.water_heater.target_temperature},'
            cjson += f'"real_target_temperature":{self._facade.water_heater.real_target_temperature}'
            cjson += '}'

            self._onValueChange(const.TOPIC_WATERHEAT, cjson)

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

            cjson = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '",'
            # cjson += '{'
            i = 0
            for reminder in reminders:
                cjson += f'"{reminder.description}":"{reminder.days}"'
                if (i < reminders_len):
                    cjson += ","
                i += 1
            cjson += '}'

            if cjson is not None:
                self._onValueChange(const.TOPIC_REMINDERS, cjson)

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
            cjson = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '",'
            cjson += f'"Filter Status:Clean":"{str(filerStatusClean).lower()}",'
            cjson += f'"Filter Status:Purge":"{str(filerStatusPurge).lower()}"'
            cjson += '}'

            self._onValueChange(const.TOPIC_FILTER_STATUS, cjson)

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
            cjson = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '",'
            cjson += f'"Smart Winter Mode:Active":"{str(swmActive).lower()}",'
            cjson += f'"Smart Winter Mode:Risk":"{str(swmRisk).lower()}"'
            cjson += '}'

            self._onValueChange(const.TOPIC_SMARTWINTERMODE, cjson)

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
            cjson = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '",'
            cjson += f'"Ozone Mode":"{str(ozoneMode).lower()}"'
            cjson += '}'

            self._onValueChange(const.TOPIC_OZONEMODE, cjson)

    ################
    #
    # Controls
    #
    ##############
    async def controls(self, client, userdata, message):
        '''
        Controlling the spa
        '''
        try:
            msg = json.loads(message.payload.decode('UTF-8'))
        except Exception as ex:
            logger.warning(f"Invalid JSON in mqtt message: {ex.args}")
        topic = str(message.topic)
        logger.debug(f'msg received: topic: {topic}, payload: {msg}')
        if "lights" in msg and self.facade.lights[0] is not None:
            if msg["lights"] == "on":
                logger.info("Switching lights on")
                await self._facade.lights[0].async_turn_on()
            elif msg["lights"] == "off":
                logger.info("Switching lights off")
                await self._facade.lights[0].async_turn_off()
        elif "pump" in msg:
            p_nbr = int(msg["number"])
            if p_nbr > len(self._facade.pumps):
                logger.warning(f"Pump %i does not exist.", p_nbr)
                return
            if msg["pump"] == "off":
                logger.info("Switching pump %i off", p_nbr)
                await self._facade.pumps[p_nbr - 1].set_mode("OFF")
            elif msg["pump"] == "low":
                logger.info("Switching pump %i to low", p_nbr)
                await self._facade.pumps[p_nbr - 1].set_mode("LO")
            elif msg["pump"] == "high":
                logger.info("Switching pump %i to high", p_nbr)
                await self._facade.pumps[p_nbr - 1].set_mode("HI")
        elif "temp" in msg:
            try:
                temp = float(msg["temp"])
            except Exception as ex:
                logger.warning(f"Wrong temperature value received")
                return
            if temp < 6 and temp > 40:
                logger.warning(f"Temperature {temp} outside allowed values")
                return
            await self._facade.water_heater.set_target_temperature(temp)
        elif "blower" in msg and self.facade.blowers[0] is not None:
            if msg["blower"] == "high":
                logger.info("Switching blower on")
                await self._facade.blowers[0].async_turn_on()
            elif msg["blower"] == "off":
                logger.info("Switching blower on")
                await self._facade.blowers[0].async_turn_off()
        elif "watercare" in msg:
            try:
                mode = int(msg["watercare"])
            except:
                logger.error(f"Wrong mode received: {mode}")
                return
            await self._facade.water_care.async_set_mode(mode)
        elif "refresh" in msg:
            if msg["refresh"] == "all":
                await self._refreshAll()
        else:
            logger.warning(f"Wrong command received")


class OnChange():
    def __init__(self, mySpa: MySpa) -> None:
        self._mySpa = mySpa

    def __call__(self, sender, old_value, new_value):
        logger.debug(f"on_spa_change: >{sender}< changed from {old_value} to {new_value}")
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
                logger.warning(f"Not handled GeckoStructAccessor sender tag received: {sender.tag}")
                logger.warning(f"  --> {sender} changed from {old_value} to {new_value}")

        else:
            logger.warning(f"Change not check. Sender: {sender}, sender-type: {sender.type()}")
