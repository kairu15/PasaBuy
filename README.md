# PasaBuy

PasaBuy is a local Django application for buyer ordering, admin inventory control, checkout, analytics, and live GPS mapping.

Although Django uses a local app server internally, this project is intended to run as a local application on the device or local network, not as a public website. Phone GPS works when the user opens the app URL from the phone and allows location permission.

## Main Features

- Buyer registration and secure username/password login
- Buyer profile with name, address, contact number, and automatic GPS location
- Item browsing, unlimited cart selection, total amount calculation, and checkout
- GCash and Cash on Delivery payment choices
- Admin login with full inventory control
- Add, edit, delete, search, and filter items
- Stock updates and seller location fields
- Admin dashboard with daily sales, recent orders, low stock, and sold-item filtering
- Live map for Admin, Seller, and Buyer locations

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Prepare the database:

```powershell
python manage.py migrate
python manage.py seed_demo
```

4. Run the local app:

```powershell
python manage.py runserver 0.0.0.0:8001
```

You can also use the included helpers:

```powershell
.\setup_pasabuy.ps1
.\run_pasabuy.ps1
```

5. Open the app:

- On the same computer: `http://127.0.0.1:8001`
- On a phone connected to the same Wi-Fi: `http://<computer-ip-address>:8001`

Allow GPS/location permission when prompted.

## Demo Accounts

Run `python manage.py seed_demo` to create:

- Admin: `admin` / `Admin12345!`
- Buyer: `buyer` / `Buyer12345!`

Change these passwords before using the app beyond local testing.

## Notes About GPS And Maps

The app uses the device geolocation API for real-time buyer/admin location updates. Seller locations are set by the admin on item records through latitude and longitude fields.

The map screen uses OpenStreetMap map tiles through Leaflet. It behaves similarly to Google Maps for marker display and panning, while avoiding the need for a Google Maps API key.
