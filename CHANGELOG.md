# Changelog

## [Unreleased]

## [2025-12-03]

### Frontend (Dashboard)
- **Auto-detect API Server**: The dashboard now automatically uses the current window origin (`window.location.origin`) as the API server address, removing the need to manually specify `http://127.0.0.1:8088` in the input field.
- **CSS Cleanup**: 
  - Removed unused `stats-container` styles.
  - Removed custom scrollbar styling for the right panel to improve compatibility.
- **Logic Updates**:
  - `BatchGenerationManager` now initializes with dynamic API server URL.
  - `submitSingle` and `refreshTasks` no longer depend on the `apiServer` DOM input value.

### Configuration
- Updated `quick_start.sh`.

