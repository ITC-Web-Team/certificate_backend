# Certificate Portal Backend 🖥️

Django-based backend for the Certificate Portal system, handling certificate generation, storage, and verification.

## Features 🌟

- **Certificate Generation**: Dynamic certificate generation with custom fields
- **Minio Storage**: Secure storage for certificates and templates
- **CSV Processing**: Bulk data handling for certificate generation
- **REST API**: Complete API for certificate management
- **PostgreSQL**: Robust database management
- **Docker Support**: Containerized deployment ready

## Tech Stack 🛠️

- Django 4.2
- Django REST Framework
- PostgreSQL
- Minio Storage
- Pillow for image processing
- Pandas for CSV handling
- Docker & Docker Compose

## API Endpoints 📡

- `POST /upload/`: Upload new certificate template
- `GET /list/<user>/`: Get user's certificates
- `GET /certificate/<id>/generate/<roll_no>/`: Generate certificate
- `DELETE /delete/<id>/<user>/`: Delete certificate
- `GET /templates/<user>/`: Get user's templates

## Setup & Installation 🚀

1. Clone the repository:

```bash
git clone https://github.com/ITC-Web-Team/certificate_portal_2.git
cd certificate_portal_2/backend
```

2. Create and activate virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

```bash
cp .env.example .env
```

5. Run migrations:

```bash
python manage.py migrate
```

6. Start the development server:

```bash
python manage.py runserver
```

## Environment Variables 🔐

```env
DJANGO_SECRET_KEY=your_secret_key
DEBUG=True
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
MINIO_STORAGE_ENDPOINT=your_minio_endpoint
```

## Docker Deployment 🐳

```bash
docker-compose up --build
```

## Contributing 🤝

See the [CONTRIBUTING.md](CONTRIBUTING.md) file for details.

## License 📄

MIT License - see the [LICENSE](LICENSE) file for details.
