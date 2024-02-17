"""Support for MelCloud device binary sensors."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Callable

from pymelcloud import DEVICE_TYPE_ATA, DEVICE_TYPE_ERV

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MelCloudDevice
from .const import DOMAIN, MEL_DEVICES


@dataclass
class MelcloudRequiredKeysMixin:
    """Mixin for required keys."""

    value_fn: Callable[[Any], bool]
    enabled: Callable[[Any], bool]


@dataclass
class MelcloudBinarySensorEntityDescription(
    BinarySensorEntityDescription, MelcloudRequiredKeysMixin
):
    """Describes Melcloud binary sensor entity."""


ATA_BINARY_SENSORS: tuple[MelcloudBinarySensorEntityDescription, ...] = (
    MelcloudBinarySensorEntityDescription(
        key="error_state",
        name="Error State",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda x: x.error_state,
        enabled=lambda x: True,
    ),
)

ERV_BINARY_SENSORS: tuple[MelcloudBinarySensorEntityDescription, ...] = (
    MelcloudBinarySensorEntityDescription(
        key="core_maintenance_required",
        name="Core maintenance required",
        icon="mdi:account-wrench",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda x: x.device.core_maintenance_required,
        enabled=lambda x: True,
        entity_registry_enabled_default=True,
    ),
    MelcloudBinarySensorEntityDescription(
        key="filter_maintenance_required",
        name="Filter maintenance required",
        icon="mdi:air-filter",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda x: x.device.core_maintenance_required,
        enabled=lambda x: True,
        entity_registry_enabled_default=True,
    ),
    MelcloudBinarySensorEntityDescription(
        key="error_state",
        name="Error State",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda x: x.error_state,
        enabled=lambda x: True,
        entity_registry_enabled_default=True,
    ),
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up MELCloud device binary sensors based on config_entry."""
    entry_config = hass.data[DOMAIN][entry.entry_id]

    mel_devices = entry_config.get(MEL_DEVICES)
    entities = []
    entities.extend(
        [
            MelDeviceBinarySensor(mel_device, description)
            for description in ATA_BINARY_SENSORS
            for mel_device in mel_devices[DEVICE_TYPE_ATA]
            if description.enabled(mel_device)
        ]
        + [
            MelDeviceBinarySensor(mel_device, description)
            for description in ERV_BINARY_SENSORS
            for mel_device in mel_devices[DEVICE_TYPE_ERV]
            if description.enabled(mel_device)
        ]
    )
    async_add_entities(entities, False)


class MelDeviceBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Binary Sensor."""

    entity_description: MelcloudBinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        api: MelCloudDevice,
        description: MelcloudBinarySensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(api.coordinator)
        self._api = api
        self.entity_description = description

        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-{description.key}"
        self._attr_device_info = api.device_info
        self._attr_extra_state_attributes = api.extra_attributes

    @property
    def is_on(self):
        """Return the state of the binary sensor."""
        return self.entity_description.value_fn(self._api)
