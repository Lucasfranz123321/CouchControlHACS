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

1. **Settings → Devices & Services** → find **Couch Control Entity Filter** → three-dot menu → **Delete**.
   This removes the config entry, unregisters the WebSocket / REST handlers, and (via `async_remove_entry`) deletes the persisted entity allowlist at `.storage/couch_control` automatically.
2. **HACS → Integrations → Couch Control → Remove** to delete the integration files from `custom_components/couch_control/`.
3. Restart Home Assistant.

> **Upgrading from 1.0.0?** That version was misclassified as `integration_type: "helper"`, which placed the card under **Helpers** instead of **Devices & Services** and hid the Delete button. After updating to 1.0.1 via HACS and restarting Home Assistant, the integration will move to **Devices & Services** and the standard delete flow above will work. If your install is still stuck on 1.0.0 and you can't update via HACS, you can manually edit `.storage/core.config_entries` and remove the block whose `"domain": "couch_control"` to clear the entry.

## Support

If you encounter any issues:

1. Check that you've selected entities in the helper configuration
2. Restart both Home Assistant and the Couch Control app
3. Report issues at: https://github.com/Lucasfranz123321/CouchControlHACS/issues

## Compatibility

- **Home Assistant**: 2023.1.0 or newer
- **Couch Control App**: Version 2.0 or newer
- **HACS**: Version 1.6.0 or newer
