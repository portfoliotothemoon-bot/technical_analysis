# Define the project directory path
$workingDir = "C:\Development\Investment\python_programs\find_moving_averages_trade_set_up"

# Set the location to the project folder
Set-Location -Path $workingDir

# Run the Python script using the specific virtual environment
& ".\.venv\Scripts\python.exe" "sma_tracker.py"

# Keep the console open
Write-Host "`nPress any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
