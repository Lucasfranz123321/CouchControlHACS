# Couch Control HACS Integration

This Home Assistant integration provides optimized entity filtering for the Couch Control tvOS app.

## What it does

The Couch Control app normally loads ALL entities from your Home Assistant server, which can cause performance issues with large instances (1000+ entities). This integration allows you to select only the entities you want to use in your widgets, dramatically improving performance and reducing network traffic.

## Installation

1. Go to HACS page in Home Assistant
2. Press on the 3 dots on the top right
3. Press on 'Custom Repositories'
4. Add this URL: https://github.com/Lucasfranz123321/CouchControlHACS as Integration
5.  Press on 'Couch Control' inside HACS and press download
6. Go to Devices & Services, press "add integration" and look for 'Couch Control'
7. Install the Couch Control integration
8. When prompted, choose the devices to expose inside Couch Control app
9. Restart Couch Control and HACS integration

## Benefits

- **Faster Loading**: Only selected entities are processed
- **Improved Performance**: Reduced memory usage and network traffic
- **Better Responsiveness**: UI updates are faster with fewer entities
- **Customizable**: Choose exactly which devices to include

## API Endpoints

This integration provides two API endpoints for the Couch Control app:

- `/api/couch_control/states` - Returns filtered entity states
- `/api/couch_control/info` - Returns integration status

## Uninstalling

**Recommended (one-service clean removal — added in 1.0.2):**

1. **Developer Tools → Services** → search for **Couch Control: Uninstall (clean removal)** → **Call Service**.
   The integration removes its own config entry and deletes the persisted entity allowlist at `.storage/couch_control` while its code is still loaded. You'll get a notification confirming success.
2. **HACS → Integrations → Couch Control → Remove** to delete the integration files.
3. Restart Home Assistant.

**Alternative (UI-only, equivalent end state):**

1. **Settings → Devices & Services** → find **Couch Control Entity Filter** → three-dot menu → **Delete**.
   Same effect as the service in step 1 above (it routes through `async_remove_entry` either way).
2. HACS → remove → restart HA.

**Why the dedicated service exists**: if you remove the integration via HACS *first*, Home Assistant can no longer call any cleanup code from this integration (the module is gone), so the config entry and `.storage/couch_control` are stranded. HA does eventually offer a "missing integration" Delete button on the orphan entry after a restart, but the persisted file lingers. Calling `couch_control.uninstall` first does the cleanup while the code is still loaded, so HACS removal afterwards has nothing left to clean.

> **Upgrading from 1.0.0?** That version was misclassified as `integration_type: "helper"`, which placed the card under **Helpers** instead of **Devices & Services** and hid the Delete button. Updating to 1.0.2 via HACS and restarting Home Assistant moves the integration to **Devices & Services** *and* gives you the new uninstall service. If your install is still stuck on 1.0.0 and you can't update via HACS, you can manually edit `.storage/core.config_entries` and remove the block whose `"domain": "couch_control"` to clear the entry.

## Support

If you encounter any issues:

1. Check that you've selected entities in the helper configuration
2. Restart both Home Assistant and the Couch Control app
3. Report issues at: https://github.com/Lucasfranz123321/CouchControlHACS/issues

## Compatibility

- **Home Assistant**: 2023.1.0 or newer
- **Couch Control App**: Version 2.0 or newer
- **HACS**: Version 1.6.0 or newer
