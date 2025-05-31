#!/bin/bash

# =============================================================================
# Enterprise CI/CD Setup Script
# =============================================================================
# This script helps implement enterprise-grade CI/CD features incrementally
# 
# Usage: ./scripts/enterprise-setup.sh [feature]
# Features: security, testing, monitoring, iac, compliance

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

print_header() {
    echo -e "${CYAN}================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}================================${NC}"
    echo
}

print_step() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

prompt_yes_no() {
    local prompt="$1"
    local default="${2:-n}"
    
    if [[ "$default" == "y" ]]; then
        prompt="$prompt [Y/n]: "
    else
        prompt="$prompt [y/N]: "
    fi
    
    while true; do
        read -p "$prompt" yn
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            "" ) 
                if [[ "$default" == "y" ]]; then
                    return 0
                else
                    return 1
                fi
                ;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

setup_security_scanning() {
    print_header "Setting Up Security Scanning"
    
    # Create security workflows directory
    mkdir -p .github/workflows
    
    print_step "Creating SAST security workflow..."
    cat > .github/workflows/security-sast.yml << 'EOF'
name: SAST Security Scan
on: 
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  sast:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      actions: read
      contents: read
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      # CodeQL Analysis for Python
      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: python
          
      - name: Autobuild
        uses: github/codeql-action/autobuild@v3
        
      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
        
      # Semgrep Security Scan
      - name: Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/security-audit
            p/secrets
            p/owasp-top-ten
            p/python
        env:
          SEMGREP_APP_TOKEN: ${{ secrets.SEMGREP_APP_TOKEN }}
EOF

    print_step "Creating container security workflow..."
    cat > .github/workflows/container-security.yml << 'EOF'
name: Container Security
on: 
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  container-scan:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Build Docker image
        run: |
          docker build -t fastapi-security-scan:${{ github.sha }} .
          
      # Trivy vulnerability scanner
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'fastapi-security-scan:${{ github.sha }}'
          format: 'sarif'
          output: 'trivy-results.sarif'
          
      - name: Upload Trivy scan results to GitHub Security tab
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'
          
      # Docker Scout (if available)
      - name: Docker Scout
        if: github.event_name == 'push'
        uses: docker/scout-action@v1
        with:
          command: cves
          image: fastapi-security-scan:${{ github.sha }}
          only-severities: critical,high
          exit-code: true
EOF

    print_success "Security scanning workflows created"
    
    # Create security policy
    print_step "Creating security policy..."
    mkdir -p .github
    cat > .github/SECURITY.md << 'EOF'
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

Please report security vulnerabilities to security@yourcompany.com

### What to include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response timeline:
- Initial response: 24 hours
- Status update: 72 hours
- Resolution target: 30 days for critical, 90 days for others
EOF

    print_success "Security policy created"
    echo
}

setup_comprehensive_testing() {
    print_header "Setting Up Comprehensive Testing"
    
    # Create test directories
    mkdir -p tests/{unit,integration,performance,contract}
    
    print_step "Creating comprehensive testing workflow..."
    cat > .github/workflows/comprehensive-testing.yml << 'EOF'
name: Comprehensive Testing
on: 
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio httpx
          
      - name: Run unit tests
        run: |
          pytest tests/unit/ -v --cov=src --cov-report=xml --cov-report=html --junitxml=junit.xml
          
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
          
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx
          
      - name: Run integration tests
        env:
          PGHOST: localhost
          PGPORT: 5432
          PGDATABASE: testdb
          PGUSER: postgres
          PGPASSWORD: test
        run: |
          pytest tests/integration/ -v

  performance-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup K6
        uses: grafana/setup-k6-action@v1
        
      - name: Run performance tests
        run: |
          k6 run tests/performance/load-test.js
EOF

    # Create sample test files
    print_step "Creating sample test files..."
    
    # Unit test example
    cat > tests/unit/test_main.py << 'EOF'
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()

def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
EOF

    # Integration test example
    cat > tests/integration/test_database.py << 'EOF'
import pytest
import asyncio
import os

@pytest.mark.asyncio
async def test_database_connection():
    """Test database connectivity."""
    # This would test actual database operations
    # For now, just check environment variables are set
    assert os.getenv('PGHOST') is not None
    assert os.getenv('PGDATABASE') is not None
    
@pytest.mark.asyncio 
async def test_api_integration():
    """Test full API integration."""
    # This would test end-to-end API functionality
    pass
EOF

    # Performance test example
    cat > tests/performance/load-test.js << 'EOF'
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 10 }, // Ramp up
    { duration: '5m', target: 10 }, // Stay at 10 users
    { duration: '2m', target: 0 },  // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
    http_req_failed: ['rate<0.1'],    // Error rate must be below 10%
  },
};

export default function() {
  let response = http.get('http://localhost:9000/health');
  
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  sleep(1);
}
EOF

    print_success "Comprehensive testing setup complete"
    echo
}

setup_monitoring() {
    print_header "Setting Up Advanced Monitoring"
    
    # Create monitoring directory
    mkdir -p monitoring/{prometheus,grafana,alerts}
    
    print_step "Creating Prometheus configuration..."
    cat > monitoring/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alerts/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['localhost:9000']
    metrics_path: '/metrics'
    scrape_interval: 5s
    
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
EOF

    print_step "Creating Grafana dashboard..."
    cat > monitoring/grafana/fastapi-dashboard.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "FastAPI Application Metrics",
    "tags": ["fastapi", "python"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{handler}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph", 
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"4..|5..\"}[5m])",
            "legendFormat": "Error rate"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "5s"
  }
}
EOF

    print_step "Creating alert rules..."
    cat > monitoring/prometheus/alerts/fastapi-alerts.yml << 'EOF'
groups:
  - name: fastapi-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"
          
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }} seconds"
          
      - alert: ServiceDown
        expr: up{job="fastapi"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "FastAPI service is down"
          description: "FastAPI service has been down for more than 1 minute"
EOF

    print_step "Creating Docker Compose for monitoring stack..."
    cat > monitoring/docker-compose.monitoring.yml << 'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
      
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana:/etc/grafana/provisioning
      
  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager:/etc/alertmanager
      
  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'

volumes:
  prometheus_data:
  grafana_data:
EOF

    print_success "Advanced monitoring setup complete"
    echo
}

setup_infrastructure_as_code() {
    print_header "Setting Up Infrastructure as Code"
    
    # Create terraform directories
    mkdir -p terraform/{modules,environments/{dev,staging,prod}}
    
    print_step "Creating Terraform module structure..."
    
    # Main module
    cat > terraform/modules/fastapi-app/main.tf << 'EOF'
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.app_name}-${var.environment}"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = var.tags
}

# ECS Task Definition
resource "aws_ecs_task_definition" "app" {
  family                   = "${var.app_name}-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = var.app_name
      image = "${var.image_repository}:${var.image_tag}"
      
      portMappings = [
        {
          containerPort = var.container_port
          protocol      = "tcp"
        }
      ]
      
      environment = [
        for key, value in var.environment_variables : {
          name  = key
          value = value
        }
      ]
      
      secrets = [
        for key, value in var.secrets : {
          name      = key
          valueFrom = value
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.app.name
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = "ecs"
        }
      }
      
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.container_port}/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
  
  tags = var.tags
}

# ECS Service
resource "aws_ecs_service" "app" {
  name            = "${var.app_name}-${var.environment}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.app.id]
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = var.app_name
    container_port   = var.container_port
  }
  
  depends_on = [aws_lb_listener.app]
  
  tags = var.tags
}
EOF

    # Variables
    cat > terraform/modules/fastapi-app/variables.tf << 'EOF'
variable "app_name" {
  description = "Name of the application"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "image_repository" {
  description = "Docker image repository"
  type        = string
}

variable "image_tag" {
  description = "Docker image tag"
  type        = string
  default     = "latest"
}

variable "cpu" {
  description = "CPU units for the task"
  type        = number
  default     = 256
}

variable "memory" {
  description = "Memory for the task"
  type        = number
  default     = 512
}

variable "desired_count" {
  description = "Desired number of tasks"
  type        = number
  default     = 2
}

variable "container_port" {
  description = "Port the container listens on"
  type        = number
  default     = 9000
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "Public subnet IDs"
  type        = list(string)
}

variable "environment_variables" {
  description = "Environment variables"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Secrets from Parameter Store"
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
EOF

    # Production environment
    cat > terraform/environments/prod/main.tf << 'EOF'
terraform {
  required_version = ">= 1.0"
  
  backend "s3" {
    bucket = "your-terraform-state-bucket"
    key    = "fastapi/prod/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = "us-east-1"
  
  default_tags {
    tags = {
      Environment = "production"
      Project     = "fastapi"
      ManagedBy   = "terraform"
    }
  }
}

module "fastapi_app" {
  source = "../../modules/fastapi-app"
  
  app_name    = "fastapi"
  environment = "production"
  
  image_repository = "your-dockerhub-username/fastapi"
  image_tag       = var.image_tag
  
  cpu           = 512
  memory        = 1024
  desired_count = 3
  
  vpc_id             = data.aws_vpc.main.id
  private_subnet_ids = data.aws_subnets.private.ids
  public_subnet_ids  = data.aws_subnets.public.ids
  
  environment_variables = {
    DD_ENV     = "production"
    DD_SERVICE = "fastapi"
    DD_VERSION = var.image_tag
  }
  
  secrets = {
    PGPASSWORD      = "/fastapi/prod/database/password"
    OPENAI_API_KEY  = "/fastapi/prod/openai/api_key"
    DATADOG_API_KEY = "/fastapi/prod/datadog/api_key"
  }
  
  tags = {
    Environment = "production"
    Application = "fastapi"
  }
}
EOF

    print_success "Infrastructure as Code setup complete"
    echo
}

setup_compliance() {
    print_header "Setting Up Compliance & Governance"
    
    # Create policies directory
    mkdir -p policies/{opa,terraform}
    
    print_step "Creating OPA policies..."
    cat > policies/opa/security-policies.rego << 'EOF'
package kubernetes.admission

# Deny containers running as root
deny[msg] {
    input.request.kind.kind == "Pod"
    input.request.object.spec.containers[_].securityContext.runAsUser == 0
    msg := "Containers must not run as root user"
}

# Require security context
deny[msg] {
    input.request.kind.kind == "Pod"
    not input.request.object.spec.securityContext
    msg := "Pod must have securityContext defined"
}

# Require resource limits
deny[msg] {
    input.request.kind.kind == "Pod"
    container := input.request.object.spec.containers[_]
    not container.resources.limits
    msg := sprintf("Container %v must have resource limits defined", [container.name])
}

# Require non-privileged containers
deny[msg] {
    input.request.kind.kind == "Pod"
    container := input.request.object.spec.containers[_]
    container.securityContext.privileged == true
    msg := sprintf("Container %v must not run in privileged mode", [container.name])
}
EOF

    print_step "Creating Terraform policies..."
    cat > policies/terraform/security.sentinel << 'EOF'
import "tfplan/v2" as tfplan

# Ensure all S3 buckets have encryption
s3_buckets_encrypted = rule {
    all tfplan.resource_changes as _, changes {
        changes.type is "aws_s3_bucket" implies
        changes.change.after.server_side_encryption_configuration is not null
    }
}

# Ensure ECS tasks don't run as root
ecs_tasks_non_root = rule {
    all tfplan.resource_changes as _, changes {
        changes.type is "aws_ecs_task_definition" implies
        all changes.change.after.container_definitions as container {
            container.user is not "root" and
            container.user is not "0"
        }
    }
}

# Ensure security groups don't allow unrestricted access
security_groups_restricted = rule {
    all tfplan.resource_changes as _, changes {
        changes.type is "aws_security_group_rule" implies
        changes.change.after.cidr_blocks does not contain "0.0.0.0/0" or
        changes.change.after.from_port is not 22
    }
}

main = rule {
    s3_buckets_encrypted and
    ecs_tasks_non_root and
    security_groups_restricted
}
EOF

    print_step "Creating compliance workflow..."
    cat > .github/workflows/compliance.yml << 'EOF'
name: Compliance & Governance
on: 
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  terraform-compliance:
    runs-on: ubuntu-latest
    if: contains(github.event.head_commit.modified, 'terraform/')
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
        
      - name: Terraform Format Check
        run: terraform fmt -check -recursive terraform/
        
      - name: Terraform Validate
        run: |
          cd terraform/environments/prod
          terraform init -backend=false
          terraform validate
          
      - name: Run Checkov
        uses: bridgecrewio/checkov-action@master
        with:
          directory: terraform/
          framework: terraform
          output_format: sarif
          output_file_path: checkov-results.sarif
          
      - name: Upload Checkov results
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: checkov-results.sarif

  docker-compliance:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker image
        run: docker build -t compliance-test .
        
      - name: Run Docker Bench Security
        run: |
          docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
            -v $(pwd):/host aquasec/docker-bench-security
            
      - name: Run Hadolint
        uses: hadolint/hadolint-action@v3.1.0
        with:
          dockerfile: Dockerfile
          format: sarif
          output-file: hadolint-results.sarif
          
      - name: Upload Hadolint results
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: hadolint-results.sarif
EOF

    print_success "Compliance & governance setup complete"
    echo
}

show_menu() {
    print_header "Enterprise CI/CD Setup"
    
    echo "Choose which enterprise features to implement:"
    echo
    echo "1. Security Scanning (SAST, Container Security)"
    echo "2. Comprehensive Testing (Unit, Integration, Performance)"
    echo "3. Advanced Monitoring (Prometheus, Grafana, Alerts)"
    echo "4. Infrastructure as Code (Terraform, AWS ECS)"
    echo "5. Compliance & Governance (OPA, Terraform policies)"
    echo "6. All of the above"
    echo "7. Exit"
    echo
}

main() {
    cd "$PROJECT_ROOT"
    
    if [[ $# -eq 1 ]]; then
        case "$1" in
            security) setup_security_scanning ;;
            testing) setup_comprehensive_testing ;;
            monitoring) setup_monitoring ;;
            iac) setup_infrastructure_as_code ;;
            compliance) setup_compliance ;;
            *) 
                print_error "Unknown feature: $1"
                echo "Available features: security, testing, monitoring, iac, compliance"
                exit 1
                ;;
        esac
        return
    fi
    
    while true; do
        show_menu
        read -p "Enter your choice (1-7): " choice
        
        case $choice in
            1) setup_security_scanning ;;
            2) setup_comprehensive_testing ;;
            3) setup_monitoring ;;
            4) setup_infrastructure_as_code ;;
            5) setup_compliance ;;
            6) 
                setup_security_scanning
                setup_comprehensive_testing
                setup_monitoring
                setup_infrastructure_as_code
                setup_compliance
                print_success "All enterprise features have been set up!"
                ;;
            7) 
                print_success "Goodbye!"
                exit 0
                ;;
            *) 
                print_error "Invalid choice. Please enter 1-7."
                ;;
        esac
        
        echo
        if prompt_yes_no "Would you like to set up another feature?"; then
            continue
        else
            break
        fi
    done
    
    print_header "Setup Complete!"
    echo -e "${GREEN}Enterprise CI/CD features have been configured.${NC}"
    echo
    echo -e "${CYAN}Next steps:${NC}"
    echo "1. Review and customize the generated configurations"
    echo "2. Set up required secrets in GitHub (API keys, tokens)"
    echo "3. Configure your cloud infrastructure (AWS, etc.)"
    echo "4. Test the workflows with a commit"
    echo "5. Monitor and iterate on your setup"
    echo
}

main "$@" 