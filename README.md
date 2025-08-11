# Couch Control HACS Integration

This Home Assistant integration provides optimized entity filtering for the Couch Control tvOS app.

## What it does

The Couch Control app normally loads ALL entities from your Home Assistant server, which can cause performance issues with large instances (1000+ entities). This integration allows you to select only the entities you want to use in your widgets, dramatically improving performance and reducing network traffic.

## Installation

1. **Install via HACS**:
   - Open HACS in Home Assistant
   - Go to "Integrations"
   - Search for "Couch Control"
   - Install the integration

2. **Add the integration**:
   - Go to Settings → Devices & Services → Helpers
   - Click "Add Helper"
   - Search for "Couch Control"
   - Select the entities you want to use in your widgets

3. **Restart your Couch Control app**:
   - The app will automatically detect the integration
   - Only selected entities will be loaded for improved performance

## Configuration

After installing the integration:

1. Go to **Settings → Devices & Services → Helpers**
2. Click **"Add Helper"** and search for **"Couch Control"**
3. Select the entities you want to use in your widgets:
   - Lights, switches, and scenes for control widgets
   - Sensors for temperature, humidity, and other data widgets
   - Media players for media control widgets
   - Weather entities for weather widgets
   - Calendar entities for calendar widgets

## Benefits

- **Faster Loading**: Only selected entities are processed
- **Improved Performance**: Reduced memory usage and network traffic
- **Better Responsiveness**: UI updates are faster with fewer entities
- **Customizable**: Choose exactly which devices to include

## API Endpoints

This integration provides two API endpoints for the Couch Control app:

- `/api/couch_control/states` - Returns filtered entity states
- `/api/couch_control/info` - Returns integration status

## Support

If you encounter any issues:

1. Check that you've selected entities in the helper configuration
2. Restart both Home Assistant and the Couch Control app
3. Report issues at: https://github.com/lucasfranz/couch-control-hacs/issues

## Compatibility

- **Home Assistant**: 2023.1.0 or newer
- **Couch Control App**: Version 2.0 or newer
- **HACS**: Version 1.6.0 or newer