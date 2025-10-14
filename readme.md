# TP-Link Archer MR200 - SMS API Docker

🚀 API REST to send SMS from TP-Link Archer MR200 4G LTE router.

## 📋 Table of Contents

- [Quick Install](#quick-install)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [License](#license)
- [Acknowledgments](#acknowledgments)

### tested versions

- TP-Link Archer MR200 
 
  Firmware Version: 1.9.0 0.9.1 v0001.0 Build 190307 Rel.54196n
  Hardware Version: Archer MR200 v4 00000001

## 🚀 Quick install

### 1. Clone the project

```bash
git clone https://github.com/votre-username/mr200-sms-api.git
cd mr200-sms-api
```

### Configuration

```env
ROUTER_IP=192.168.1.1        # MR200 IP
ROUTER_PASSWORD=<password>         # admin password
```


### Commands

```bash
# Check health
curl http://localhost:5333/health

# Send a test SMS
curl -X POST http://localhost:5333/send_sms \
  -H "Content-Type: application/json" \
  -d '{"phone":"+3312345678","message":"Test SMS"}'
```

### project files

TODO


## 📖 API Documentation

### Endpoints

#### `POST /send_sms`

Send an SMS.

**Request:**
```json
{
    "phone": "+3312345678",
    "message": "your message"
}
```

Alternative accepted formats:
```json
{"to": "+3312345678", "text": "Message"}
{"number": "+3312345678", "content": "Message"}
```

**Response Success (200):**
```json
{
    "success": true,
    "message": "SMS sent successfully",
    "to": "+3312345678"
}
```

**Response Error (500):**
```json
{
    "success": false,
    "error": "Failed to send SMS",
    "details": "Check logs for more information"
}
```

#### `GET /health`

Check the service status.

**Response:**
```json
{
    "status": "ok",
    "router": "192.168.1.1",
    "connected": true
}
```

#### `POST /reconnect`

Force reconnection to the router.

**Response:**
```json
{
    "success": true,
    "message": "Reconnected to router successfully"
}
```

#### `GET /`

Home page with interactive documentation.

### Authentication Process

1. **GET /cgi/getParm** → Retrieves `nn` and `ee` (RSA public keys)
2. **Encryption** → Encodes the password in Base64 then encrypts with RSA
3. **POST /cgi/login** → Sends encrypted credentials
4. **Cookies** → Retrieves JSESSIONID and other session cookies
5. **GET /** → Retrieves the token (optional)
6. **POST /cgi?2** → Sends the SMS with cookies + token


## 📝 License

MIT License - See [LICENSE](LICENSE) for more details.

## 👏 Acknowledgments

- [plewin/tp-link-modem-router](https://github.com/plewin/tp-link-modem-router)

---

⭐ **If this project helps you, feel free to give it a star!**
