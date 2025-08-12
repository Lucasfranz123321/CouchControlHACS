# Couch Control HACS Integration Troubleshooting Guide

## Problem Summary
The devices/entities selected in the HACS Couch Control integration UI aren't appearing in the tvOS app, even though the app is connecting to Home Assistant and loading entities.

## Root Cause Analysis

### Architecture Overview
The system has two components:

1. **HACS Integration** (Home Assistant side)
   - Provides a config UI to select entities
   - Exposes REST and WebSocket APIs
   - Filters entities server-side for performance

2. **tvOS App** (Client side)
   - Connects to Home Assistant WebSocket
   - Detects HACS integration via `/api/couch_control/info`
   - Sends widget entity list to HACS integration
   - Uses filtered WebSocket subscription when available

### Fixed Issues

#### 1. Missing WebSocket API Setup
**Problem**: The `__init__.py` wasn't setting up the WebSocket API endpoints that the tvOS app expects.

**Fix**: Updated `__init__.py` to call `async_setup_websocket_api(hass)` and `async_setup_api(hass)`.

#### 2. Missing Constants
**Problem**: WebSocket constants (`WS_TYPE_*`) and storage constants were missing from `const.py`.

**Fix**: Added all required constants to `const.py`.

#### 3. Missing Clear Endpoint
**Problem**: tvOS app was calling `/api/couch_control/clear` but the endpoint didn't exist.

**Fix**: Added `CouchControlClearView` to handle clear requests.

#### 4. API vs Config Entity Isolation
**Problem**: The legacy states endpoint only read from config entries, not from API updates.

**Fix**: Modified `CouchControlStatesView` to merge entities from both sources.

## Testing the Fix

### 1. Verify HACS Integration Detection
In the tvOS app logs, look for:
```
🔍 HAStore: Checking for Couch Control HACS integration...
✅ HAStore: Couch Control HACS integration detected - will use filtered WebSocket
```

If you see this, the integration is detected correctly.

### 2. Verify Entity Updates
When the app starts or widgets change, look for:
```
🎯 HAStore: Updated HACS entity filter with X entities
```

### 3. Verify WebSocket Filtering
When connecting, look for:
```
📡 HAStore: Subscribing to FILTERED state_changed events via HACS integration
```

### 4. Check Home Assistant Logs
In Home Assistant, look for:
```
INFO (MainThread) [custom_components.couch_control] Setting up Couch Control integration
INFO (MainThread) [custom_components.couch_control] Couch Control APIs registered successfully
INFO (MainThread) [custom_components.couch_control.api] Updated Couch Control entities via API: X entities
```

## Manual Testing Steps

### Step 1: Verify Integration is Active
1. Go to **Settings** → **Devices & Services**
2. Look for **Couch Control** integration
3. Click **Configure** and select some entities
4. Click **Save**

### Step 2: Check API Endpoints
Test these URLs in your browser (replace with your HA URL and add auth token):

- `http://your-ha-ip:8123/api/couch_control/info` - Should return integration info
- `http://your-ha-ip:8123/api/couch_control/entities` - Should return entity list

### Step 3: Monitor tvOS App Behavior
1. Open the tvOS app
2. Check if it detects the HACS integration (logs should show "HACS integration detected")
3. Add a Home Assistant widget
4. Verify the app sends entity list to HACS integration

### Step 4: Verify Two-Way Communication

**From Config UI to App:**
1. Add entities in HACS integration config UI
2. Restart tvOS app
3. Those entities should be available for widget selection

**From App to Config:**
1. Create widgets using specific entities in the app
2. Check `/api/couch_control/entities` endpoint
3. Those entities should appear in the API response

## Expected Behavior

### When Working Correctly:
1. **Integration Setup**: User selects entities in HACS integration UI
2. **App Detection**: tvOS app detects integration and switches to filtered mode
3. **Entity Synchronization**: App sends its widget entity list to integration
4. **Combined Filtering**: Integration serves both UI-selected and app-used entities
5. **Performance**: Only relevant entities are sent via WebSocket

### Debug Entity Flow:
```
[HACS Integration Config UI] → Select entities → Storage
                                        ↓
[tvOS App] → Detects integration → Sends widget entities → API
                                        ↓
[Combined Entity List] → WebSocket filtering → Reduced traffic
```

## Common Issues

### Issue: Integration Not Detected
**Symptoms**: App uses standard WebSocket mode
**Causes**: 
- Integration not installed properly
- `/api/couch_control/info` endpoint not responding
- Authentication issues

**Solutions**:
- Reinstall integration using `fix_and_reinstall.sh`
- Check Home Assistant logs for errors
- Verify access token is valid

### Issue: Entities Not Updating
**Symptoms**: App entities don't appear in HACS integration
**Causes**:
- `/api/couch_control/entities` endpoint not working
- WebSocket API not set up
- Storage system not initialized

**Solutions**:
- Check `async_setup_api()` is called in `__init__.py`
- Verify storage system is loading/saving properly
- Check WebSocket registration

### Issue: Performance Problems
**Symptoms**: App is slow, receiving all entities
**Causes**:
- Filtered WebSocket not working
- Integration detected but filtering disabled
- WebSocket subscription using wrong message type

**Solutions**:
- Verify WebSocket uses `couch_control/subscribe_filtered` type
- Check integration state in app logs
- Monitor WebSocket message volume

## Log Analysis Guide

### Key Log Messages to Look For:

**Success Indicators:**
- `✅ HAStore: Couch Control HACS integration detected`
- `✅ HAStore: Updated HACS entity filter with X entities`
- `📡 HAStore: Subscribing to FILTERED state_changed events`
- `INFO [custom_components.couch_control] Couch Control APIs registered successfully`

**Warning Signs:**
- `⚠️ HAStore: Failed to update HACS entity filter`
- `❌ HAStore: Search request failed`
- `ERROR [custom_components.couch_control]`
- `📡 HAStore: Subscribing to ALL state_changed events` (should be FILTERED)

**Performance Indicators:**
- `📊 HAStore Performance: Metrics: X/Y processed (Z% filtered)` (should show high filter percentage)
- `⚡ HAStore: Widget entities loaded in 0.Xs - UI is now responsive!`

## Next Steps

1. **Apply the fixes** by reinstalling the HACS integration
2. **Test the API endpoints** manually to verify they work
3. **Monitor both app and HA logs** during operation
4. **Create a test widget** to verify end-to-end functionality
5. **Measure performance** - should see significant entity filtering

If issues persist after applying these fixes, the problem may be in the entity ID matching logic between the app and Home Assistant.