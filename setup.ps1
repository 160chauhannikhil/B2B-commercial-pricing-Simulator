# setup.ps1
# Run this from PowerShell inside the commercial-pricing-simulator folder.
# Sets up a virtual environment, installs dependencies, and launches the app.

Write-Host "Creating virtual environment..." -ForegroundColor Cyan
python -m venv venv

Write-Host "Activating virtual environment..." -ForegroundColor Cyan
.\venv\Scripts\Activate.ps1

Write-Host "Installing dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host "Regenerating data, Excel model, and notebook (optional, already included)..." -ForegroundColor Cyan
python src\generate_data.py
python src\build_excel_model.py

Write-Host "Launching Streamlit app..." -ForegroundColor Green
streamlit run app.py
