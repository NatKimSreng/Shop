# Proxmox Deployment Guide for Shop E-commerce

## 🚨 Critical Issues Fixed

### 1. **Database Persistence Issues**
- **Problem**: SQLite file-based database causing data loss in containers
- **Solution**: Migrate to PostgreSQL with proper volume mounting
- **Impact**: Prevents order data, user accounts, and product information loss

### 2. **Telegram Bot Reliability**
- **Problem**: Hardcoded chat ID and poor error handling
- **Solution**: Environment-based configuration with retry logic
- **Impact**: Ensures order notifications are delivered consistently

### 3. **Session Management**
- **Problem**: Session data lost on container restarts
- **Solution**: Redis-based session storage
- **Impact**: Maintains user cart and login sessions

## 🛠️ Proxmox Setup Instructions

### Step 1: Create PostgreSQL Container

```bash
# Create PostgreSQL container
pct create 100 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname postgres-shop \
  --memory 1024 \
  --cores 1 \
  --rootfs local-lvm:8 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp

# Start container
pct start 100

# Enter container
pct enter 100
```

### Step 2: Install PostgreSQL

```bash
# Update system
apt update && apt upgrade -y

# Install PostgreSQL
apt install postgresql postgresql-contrib -y

# Start PostgreSQL service
systemctl start postgresql
systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE shop_db;"
sudo -u postgres psql -c "CREATE USER shop_user WITH PASSWORD 'shop_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE shop_db TO shop_user;"
sudo -u postgres psql -c "ALTER USER shop_user CREATEDB;"
```

### Step 3: Create Redis Container

```bash
# Create Redis container
pct create 101 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname redis-shop \
  --memory 512 \
  --cores 1 \
  --rootfs local-lvm:4 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp

# Start container
pct start 101

# Enter container
pct enter 101

# Install Redis
apt update && apt install redis-server -y
systemctl start redis-server
systemctl enable redis-server
```

### Step 4: Configure Django Application Container

```bash
# Create Django container
pct create 102 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname shop-app \
  --memory 2048 \
  --cores 2 \
  --rootfs local-lvm:10 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp

# Start container
pct start 102

# Enter container
pct enter 102
```

### Step 5: Install Python and Dependencies

```bash
# Update system
apt update && apt upgrade -y

# Install Python and dependencies
apt install python3 python3-pip python3-venv nginx git -y

# Clone your repository
git clone https://github.com/Projecy-team5/Shop.git /opt/shop
cd /opt/shop

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### Step 6: Configure Environment Variables

```bash
# Create environment file
cat > /opt/shop/.env << EOF
# Database Configuration
DB_NAME=shop_db
DB_USER=shop_user
DB_PASSWORD=shop_password
DB_HOST=192.168.1.100  # PostgreSQL container IP
DB_PORT=5432

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=7875498577:AAHaoHdqWX390E_GI08v4gBe78izt76r4Rc
TELEGRAM_CHAT_ID=-4862435107

# Redis Configuration
REDIS_URL=redis://192.168.1.101:6379/0  # Redis container IP

# Django Settings
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1,192.168.1.102
EOF

# Load environment variables
export $(cat /opt/shop/.env | xargs)
```

### Step 7: Migrate Database

```bash
# Run migration script
cd /opt/shop
python migrate_to_postgresql.py

# Or manually run migrations
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
```

### Step 8: Configure Nginx

```bash
# Create Nginx configuration
cat > /etc/nginx/sites-available/shop << EOF
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /opt/shop/staticfiles/;
    }

    location /media/ {
        alias /opt/shop/static/images/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/shop /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
```

### Step 9: Create Systemd Service

```bash
# Create service file
cat > /etc/systemd/system/shop.service << EOF
[Unit]
Description=Shop Django Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/shop
EnvironmentFile=/opt/shop/.env
ExecStart=/opt/shop/venv/bin/python manage.py runserver 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable shop
systemctl start shop
```

## 🔧 Troubleshooting

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -h 192.168.1.100 -U shop_user -d shop_db

# Check Django database connection
cd /opt/shop
source venv/bin/activate
python manage.py dbshell
```

### Telegram Bot Issues

```bash
# Test Telegram bot
cd /opt/shop
source venv/bin/activate
python test_telegram.py

# Check bot configuration
python get_group_chat_id.py
```

### Redis Connection Issues

```bash
# Test Redis connection
redis-cli -h 192.168.1.101 ping

# Check Redis logs
journalctl -u redis-server
```

## 📊 Monitoring and Backup

### Automated Backups

```bash
# Create backup script
cat > /opt/shop/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"

mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h 192.168.1.100 -U shop_user shop_db > $BACKUP_DIR/shop_db_$DATE.sql

# Static files backup
tar -czf $BACKUP_DIR/static_files_$DATE.tar.gz /opt/shop/staticfiles/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x /opt/shop/backup.sh

# Add to crontab
echo "0 2 * * * /opt/shop/backup.sh" | crontab -
```

### Health Checks

```bash
# Create health check script
cat > /opt/shop/health_check.sh << 'EOF'
#!/bin/bash

# Check Django application
if ! curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "Django application is down"
    systemctl restart shop
fi

# Check PostgreSQL
if ! pg_isready -h 192.168.1.100 -p 5432 > /dev/null 2>&1; then
    echo "PostgreSQL is down"
fi

# Check Redis
if ! redis-cli -h 192.168.1.101 ping > /dev/null 2>&1; then
    echo "Redis is down"
fi
EOF

chmod +x /opt/shop/health_check.sh

# Add to crontab
echo "*/5 * * * * /opt/shop/health_check.sh" | crontab -
```

## 🔒 Security Recommendations

### 1. **Firewall Configuration**
```bash
# Allow only necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

### 2. **SSL Certificate**
```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Get SSL certificate
certbot --nginx -d your-domain.com
```

### 3. **Database Security**
```bash
# Configure PostgreSQL for remote connections
echo "host shop_db shop_user 192.168.1.0/24 md5" >> /etc/postgresql/*/main/pg_hba.conf
systemctl restart postgresql
```

## 📈 Performance Optimization

### 1. **Database Optimization**
```sql
-- Add indexes for better performance
CREATE INDEX idx_order_user ON payment_order(user_id);
CREATE INDEX idx_order_date ON payment_order(created_at);
CREATE INDEX idx_product_category ON store_product(category_id);
```

### 2. **Caching Configuration**
```python
# Add to settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://192.168.1.101:6379/1',
    }
}
```

## 🚀 Deployment Checklist

- [ ] PostgreSQL container created and configured
- [ ] Redis container created and configured
- [ ] Django application container created
- [ ] Environment variables configured
- [ ] Database migrated from SQLite to PostgreSQL
- [ ] Nginx configured and SSL certificate installed
- [ ] Systemd service created and enabled
- [ ] Backup script configured
- [ ] Health check script configured
- [ ] Firewall configured
- [ ] Telegram bot tested
- [ ] Application tested thoroughly

## 📞 Support

If you encounter issues:
1. Check container logs: `pct enter <container_id>`
2. Check application logs: `journalctl -u shop -f`
3. Test database connection
4. Verify Telegram bot configuration
5. Check network connectivity between containers 