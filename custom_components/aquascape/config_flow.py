"""Config flow for the Aquascape integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AquascapeAPIError, AquascapeAuthError, AquascapeClient
from .const import (
    CONF_BASE_URL,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    DEFAULT_BASE_URL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): str,
        vol.Required(CONF_TOKEN): str,
        vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
    }
)


class AquascapeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Aquascape."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step where the user pastes a token."""
        errors: dict[str, str] = {}

        if user_input is not None:
            token = user_input[CONF_TOKEN].strip()
            base_url = user_input.get(CONF_BASE_URL, DEFAULT_BASE_URL).strip().rstrip("/")
            await self.async_set_unique_id(token)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            client = AquascapeClient(session, token, base_url=base_url)
            try:
                connected = await client.is_connected()
            except AquascapeAuthError:
                errors["base"] = "invalid_auth"
            except AquascapeAPIError:
                errors["base"] = "cannot_connect"
            else:
                if not connected:
                    # Token is valid but the device is offline. Allow the
                    # user to proceed — they may want to set it up before
                    # plugging in the hub.
                    _LOGGER.warning(
                        "Aquascape hub for %s reports hardware disconnected",
                        user_input[CONF_NAME],
                    )
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_TOKEN: token,
                        CONF_BASE_URL: base_url,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow handler."""
        return AquascapeOptionsFlow(config_entry)


class AquascapeOptionsFlow(OptionsFlow):
    """Allow the user to tweak the poll interval after setup."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        schema = vol.Schema(
            {
                vol.Optional(CONF_SCAN_INTERVAL, default=current): vol.All(
                    int, vol.Range(min=10, max=600)
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
