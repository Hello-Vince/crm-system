#!/bin/bash
# Script to initialize all databases with proper schemas

set -e

echo "🗄️  Creating PostgreSQL databases..."

# Wait for PostgreSQL to be ready
until docker compose exec -T postgres pg_isready -U crm_admin; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

# Create databases if they don't exist
docker compose exec -T postgres psql -U crm_admin -tc "SELECT 1 FROM pg_database WHERE datname = 'identity_db'" | grep -q 1 || \
  docker compose exec -T postgres psql -U crm_admin -c "CREATE DATABASE identity_db;"

docker compose exec -T postgres psql -U crm_admin -tc "SELECT 1 FROM pg_database WHERE datname = 'crm_db'" | grep -q 1 || \
  docker compose exec -T postgres psql -U crm_admin -c "CREATE DATABASE crm_db;"

docker compose exec -T postgres psql -U crm_admin -tc "SELECT 1 FROM pg_database WHERE datname = 'audit_db'" | grep -q 1 || \
  docker compose exec -T postgres psql -U crm_admin -c "CREATE DATABASE audit_db;"

docker compose exec -T postgres psql -U crm_admin -tc "SELECT 1 FROM pg_database WHERE datname = 'notification_db'" | grep -q 1 || \
  docker compose exec -T postgres psql -U crm_admin -c "CREATE DATABASE notification_db;"

echo "✅ Databases created successfully"

echo "🔄 Running Django migrations..."

# Create migrations first
echo "Creating migrations for identity-service..."
docker compose exec identity-service python manage.py makemigrations companies
docker compose exec identity-service python manage.py makemigrations users

echo "Creating migrations for crm-service..."
docker compose exec crm-service python manage.py makemigrations customers

echo "Creating migrations for audit-service..."
docker compose exec audit-service python manage.py makemigrations logs

echo "Creating migrations for notification-service..."
docker compose exec notification-service python manage.py makemigrations notifications

# Run migrations for each service
docker compose exec identity-service python manage.py migrate --noinput
docker compose exec crm-service python manage.py migrate --noinput
docker compose exec audit-service python manage.py migrate --noinput
docker compose exec notification-service python manage.py migrate --noinput

echo "✅ All migrations completed"

echo ""
echo "🌱 Seeding initial data (superuser + sample companies)..."
docker compose exec identity-service python manage.py seed_data

echo ""
echo "📊 Creating Kafka topics..."

# Create Kafka topics
docker compose exec kafka kafka-topics --create --if-not-exists \
  --bootstrap-server localhost:9092 \
  --topic crm.customer.created \
  --partitions 3 \
  --replication-factor 1

docker compose exec kafka kafka-topics --create --if-not-exists \
  --bootstrap-server localhost:9092 \
  --topic crm.customer.updated \
  --partitions 3 \
  --replication-factor 1

docker compose exec kafka kafka-topics --create --if-not-exists \
  --bootstrap-server localhost:9092 \
  --topic identity.company.created \
  --partitions 3 \
  --replication-factor 1

echo "✅ Kafka topics created"
echo ""
echo "🎉 System initialization complete!"
echo ""
echo "📋 Test Credentials:"
echo "   🔐 System Admin (Django Admin):"
echo "      Email: admin@crm.com"
echo "      Password: admin123"
echo "      Access: http://localhost:8001/admin"
echo ""
echo "   🏢 Company Admin:"
echo "      Email: admin.acme@crm.com"
echo "      Password: acme123"
echo ""
echo "   👤 Regular User:"
echo "      Email: user.west@crm.com"
echo "      Password: west123"
echo ""
echo "📍 Service URLs:"
echo "  - Frontend: http://localhost:3000"
echo "  - Gateway: http://localhost:4000/graphql"
echo "  - Identity Service: http://localhost:8001/graphql"
echo "  - CRM Service: http://localhost:8002/graphql"
echo "  - Audit Service: http://localhost:8003/admin"
echo "  - Notification Service: http://localhost:8004/graphql"
echo ""