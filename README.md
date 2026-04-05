# ChainVista

ChainVista is a **blockchain-enabled supply chain tracking and management system** that combines real-time IoT monitoring, shipment tracking, and blockchain verification to provide complete visibility and authenticity for supply chain operations.

## 🌟 Key Features

- **Real-Time Shipment Tracking**: Monitor shipments across multiple carriers with live GPS coordinates and status updates
- **IoT Device Integration**: Connect temperature, humidity, and multi-sensor devices for environmental monitoring
- **Blockchain Passports**: Issue and verify digital product passports with immutable blockchain records
- **NFT Minting**: Create NFTs for verified shipments and products
- **Intelligent Alerts**: Real-time alerts for temperature breaches, delays, and anomalies
- **Analytics Dashboard**: Comprehensive insights into shipment status, sensor trends, and supply chain throughput
- **Live Simulation**: Dynamic waypoint-based route simulation for realistic shipment movement

## 🏗️ Architecture

**Backend**: Flask REST API with SQLite database  
**Frontend**: Interactive HTML5 dashboard with real-time updates  
**Deployment**: Render.com (see `render.yaml`)

## 📋 Prerequisites

- Python 3.12+
- pip (Python package manager)

## 🚀 Quick Start

### Local Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Abhishekverma3205/ChainVista.git
   cd ChainVista
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Access the dashboard**:
   Open your browser and navigate to `http://localhost:5000`

## 📦 Dependencies

- **Flask**: Web framework
- **Flask-CORS**: Cross-origin resource sharing
- **Gunicorn**: WSGI HTTP server (for production)

See `requirements.txt` for the complete list.

## 🔌 API Endpoints

### Dashboard
- **GET** `/api/dashboard` - Retrieve wallet, network, and IoT metrics

### Shipments
- **GET** `/api/shipments` - List all shipments
- **GET** `/api/shipments/<id>` - Get shipment details
- **POST** `/api/shipments` - Create new shipment
- **PUT** `/api/shipments/<id>/status` - Update shipment status
- **GET** `/api/tracking` - Get real-time tracking coordinates

### IoT & Sensors
- **GET** `/api/iot/trends` - 7-day temperature and humidity trends
- **GET** `/api/iot/live` - Live sensor readings
- **GET** `/api/sensor/distribution` - Device distribution by type

### Alerts
- **GET** `/api/alerts` - Retrieve alerts (active by default)
- **PUT** `/api/alerts/<id>/resolve` - Mark alert as resolved

### Analytics
- **GET** `/api/analytics/shipment-status` - Status distribution
- **GET** `/api/analytics/temperature-history` - Temperature analytics
- **GET** `/api/analytics/throughput` - Shipment throughput (7 days)

### Blockchain & Passports
- **GET** `/api/blockchain/activity` - Recent blockchain transactions
- **POST** `/api/passport/issue` - Issue digital product passport
- **POST** `/api/passport/update` - Update passport details
- **GET** `/api/passport/view` - View all passports
- **POST** `/api/passport/verify` - Verify passport on blockchain
- **POST** `/api/passport/mint` - Mint NFT for verified passport

### Live Updates
- **GET** `/api/shipments/live-update` - Simulate shipment movement and sensor drift

## 🗄️ Database Schema

The application uses SQLite with the following tables:

- **shipments**: Core shipment data with location and sensor readings
- **alerts**: System alerts and notifications
- **blockchain_activity**: Blockchain transaction history
- **passports**: Digital product passports
- **iot_readings**: Time-series sensor data
- **devices**: Connected IoT devices

## 🌐 Deployment

### Deploy to Render.com

The project is configured for seamless deployment to Render.com:

1. Push your code to GitHub
2. Connect your Render.com account
3. Create a new Web Service pointing to this repository
4. Render will automatically execute the build and start commands from `render.yaml`

**Live Demo**: [https://chain-vista-c1c0.onrender.com/](https://chain-vista-c1c0.onrender.com/)

## 📊 Use Cases

- **Pharmaceutical Supply Chain**: Track temperature-sensitive medications with real-time alerts
- **Cold Chain Logistics**: Monitor frozen goods and perishables
- **Luxury Goods**: Verify authenticity with blockchain passports and NFTs
- **Electronics**: Track high-value components from manufacture to delivery
- **Industrial Equipment**: Monitor hazardous goods and equipment movement

## 🔒 Security Features

- CORS enabled for secure cross-origin requests
- Data integrity verified through blockchain hashing
- Immutable transaction records on blockchain
- Unique shipment and passport identifiers

## 📝 Sample Data

The application comes pre-loaded with:
- 12 sample shipments across Indian cities
- 5 IoT devices (sensors and GPS trackers)
- Historical alerts and blockchain activities
- 7-day sensor reading history

## 🛠️ Development

### File Structure
- `app.py` - Main Flask application with all API endpoints
- `index.html` - Frontend dashboard UI
- `requirements.txt` - Python dependencies
- `render.yaml` - Render.com deployment configuration

### Adding New Shipments

Send a POST request to `/api/shipments`:
```json
{
  "product": "Medical Supplies",
  "origin": "Delhi",
  "destination": "Mumbai",
  "carrier": "FastCargo India",
  "eta": "2026-04-10",
  "lat": 28.6139,
  "lng": 77.2090
}
```

## 📄 License

This project is open source and available on GitHub.

## 👨‍💻 Author

**Abhishek Verma**  
GitHub: [@Abhishekverma3205](https://github.com/Abhishekverma3205)

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to improve the project.

---

**Last Updated**: 2026-04-05 10:45:41  
**Status**: Active Development