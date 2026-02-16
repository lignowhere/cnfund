# RD-Agent Vietnam Stock Pipeline - Implementation Plan

## Executive Summary

This plan outlines the implementation of a comprehensive R&D → backtest → recommendation pipeline for Vietnamese stocks using Microsoft's RD-Agent and Qlib frameworks. The system will integrate with TCBS, VCI, and CafeF data sources to analyze 735 Vietnamese stocks, generate AI-driven factors and models, and produce daily trading recommendations.

## Research Summary

### RD-Agent Key Findings

**Architecture:**
- RD-Agent(Q) is a data-centric, multi-agent framework for automated quantitative strategy R&D
- Achieves ~2× higher ARR than benchmark factor libraries with 70% fewer factors
- Supports scenarios: fin_quant (full pipeline), fin_factor (factor generation), fin_model (model optimization)

**Key Components:**
1. Hypothesis Generation - AI-driven idea generation
2. Experiment Design - Automated experiment setup
3. Factor Coding - Implementation of alpha factors
4. Model Development - ML model selection and tuning
5. Runner/Summarizer - Execution and results analysis

**Configuration Requirements:**
- Python 3.10/3.11 with Conda environment
- LLM backend (OpenAI/Azure/LiteLLM)
- Docker for sandboxed execution
- Qlib data in binary format

### Qlib Key Findings

**Data Format:**
- Uses specialized .bin format for performance
- Required CSV columns: symbol, date, open, close, high, low, volume, factor
- Factor field = adjusted_price / original_price
- Suspended stocks: OHLCV set to NaN

**Backtest Capabilities:**
- Built-in metrics: IC, Sharpe, ARR, max drawdown, turnover
- Position/trade logging for audit
- Train/test window configuration
- Portfolio optimization modules

**Integration Points:**
- qlib.data for data management
- qlib.model for ML models
- qlib.backtest for simulation
- qlib.contrib.evaluate for metrics

### Integration Strategy

1. **Data Flow:** TCBS/VCI/CafeF → CSV → Qlib Binary → RD-Agent
2. **Factor Pipeline:** Classical factors + TCBS fundamentals + RD-Agent AI factors
3. **Model Pipeline:** RD-Agent suggestions → Qlib training → Backtest validation
4. **Output:** Daily recommendations with explainability

## Architecture Design

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        RD-Agent Vietnam Pipeline                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Data Sources │───▶│ Preprocessing│───▶│ Qlib Storage │      │
│  │ TCBS/VCI/    │    │ Clean/Norm   │    │ Binary Format│      │
│  │ CafeF        │    │ UTC+7→UTC    │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                                         │              │
│         ▼                                         ▼              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ RD-Agent     │───▶│ Factor       │───▶│ Model        │      │
│  │ Hypothesis   │    │ Engineering  │    │ Training     │      │
│  │ Generation   │    │ Classical+AI │    │ ML Pipeline  │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                   │              │
│                                                   ▼              │
│                              ┌──────────────┐    ┌──────────┐   │
│                              │ Backtest     │───▶│ Recommend│   │
│                              │ 2015-2024    │    │ Generator│   │
│                              └──────────────┘    └──────────┘   │
│                                                        │         │
│                                                        ▼         │
│                                          ┌────────────────────┐  │
│                                          │ Output:            │  │
│                                          │ - YYYYMMDD.csv     │  │
│                                          │ - report.json      │  │
│                                          │ - logs/            │  │
│                                          └────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
rd_vietnam_pipeline/
├── .env.example                    # Environment configuration template
├── docker-compose.yml              # Container orchestration
├── Dockerfile                      # Container image definition
├── Makefile                        # Build and run commands
├── README.md                       # Project documentation
├── requirements.txt                # Python dependencies
├── setup.py                        # Package installation
├── cli.py                          # Main CLI entry point
│
├── config/                         # Configuration files
│   ├── __init__.py
│   ├── settings.py                # Global settings management
│   ├── data_sources.yaml          # API endpoints, rate limits
│   ├── rdagent_config.yaml        # RD-Agent scenario configs
│   ├── qlib_config.yaml           # Qlib data and model settings
│   ├── backtest_windows.yaml     # Train/test period definitions
│   └── logging_config.yaml        # Logging configuration
│
├── ingest/                         # Data ingestion layer
│   ├── __init__.py
│   ├── base_adapter.py            # Abstract base adapter
│   ├── tcbs_adapter.py            # TCBS API integration
│   ├── vci_adapter.py             # VCI API integration
│   ├── cafef_scraper.py           # CafeF web scraper
│   ├── vnstock_fallback.py        # Backup data source
│   ├── rate_limiter.py            # API rate limiting
│   ├── cache_manager.py           # 24-hour cache layer
│   └── data_validator.py          # Quality checks
│
├── preprocessing/                  # Data preprocessing
│   ├── __init__.py
│   ├── cleaner.py                 # Missing data, outliers
│   ├── normalizer.py              # Price adjustments
│   ├── timezone_converter.py      # UTC+7 to UTC
│   ├── qlib_formatter.py          # CSV to Qlib binary
│   └── feature_engineer.py        # Technical indicators
│
├── rdagent_adapters/              # RD-Agent integration
│   ├── __init__.py
│   ├── vietnam_data_adapter.py    # Custom data loader
│   ├── hypothesis_generator.py    # AI hypothesis creation
│   ├── factor_generator.py        # AI factor suggestions
│   ├── model_suggester.py         # Model architecture ideas
│   ├── experiment_runner.py       # Experiment execution
│   └── summarizer.py              # Results analysis
│
├── factors/                        # Factor library
│   ├── __init__.py
│   ├── base_factor.py             # Factor interface
│   ├── classical_factors.py       # Momentum, value, volatility
│   ├── technical_factors.py       # RSI, MACD, Bollinger
│   ├── fundamental_factors.py     # P/E, ROE, debt ratios
│   ├── tcbs_factors.py           # TCBS-specific factors
│   ├── rdagent_factors.py        # AI-generated factors
│   └── factor_registry.py        # Factor management
│
├── models/                         # Model training
│   ├── __init__.py
│   ├── base_model.py              # Model interface
│   ├── linear_models.py           # Ridge, Lasso
│   ├── tree_models.py             # XGBoost, LightGBM
│   ├── neural_models.py           # LSTM, Transformer
│   ├── trainer.py                 # Training pipeline
│   ├── optimizer.py               # Hyperparameter tuning
│   └── model_registry.py          # Model versioning
│
├── backtest/                       # Backtesting engine
│   ├── __init__.py
│   ├── runner.py                  # Backtest executor
│   ├── portfolio.py               # Position management
│   ├── metrics.py                 # Performance metrics
│   ├── risk_manager.py            # Risk controls
│   └── report_generator.py        # Results formatting
│
├── recommendations/                # Output generation
│   ├── __init__.py
│   ├── generator.py               # Recommendation logic
│   ├── ranker.py                  # Stock ranking
│   ├── explainer.py               # SHAP/feature importance
│   ├── formatter.py               # CSV/JSON output
│   └── validator.py               # Sanity checks
│
├── api/                           # Optional REST API
│   ├── __init__.py
│   ├── server.py                  # FastAPI application
│   ├── routes.py                  # API endpoints
│   ├── schemas.py                 # Pydantic models
│   └── dependencies.py            # DI configuration
│
├── utils/                         # Utilities
│   ├── __init__.py
│   ├── logger.py                  # Logging utilities
│   ├── exceptions.py              # Custom exceptions
│   ├── decorators.py              # Retry, cache decorators
│   └── helpers.py                 # Common functions
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── conftest.py               # Pytest fixtures
│   ├── test_ingest.py            # Ingestion tests
│   ├── test_preprocessing.py     # Preprocessing tests
│   ├── test_factors.py           # Factor tests
│   ├── test_models.py            # Model tests
│   ├── test_backtest.py          # Backtest tests
│   ├── test_recommendations.py   # Output tests
│   └── test_integration.py       # End-to-end tests
│
├── data/                          # Data storage
│   ├── raw/                       # Original API data
│   │   ├── tcbs/                 # TCBS downloads
│   │   ├── vci/                  # VCI downloads
│   │   └── cafef/                # CafeF scrapes
│   ├── processed/                 # Qlib-ready data
│   │   ├── qlib_data/            # Binary format
│   │   └── features/             # Feature matrices
│   ├── cache/                    # Temporary cache
│   └── sample/                   # Demo dataset
│
├── notebooks/                     # Jupyter notebooks
│   ├── 01_data_exploration.ipynb
│   ├── 02_factor_analysis.ipynb
│   ├── 03_model_comparison.ipynb
│   └── 04_end_to_end_demo.ipynb
│
├── scripts/                       # Utility scripts
│   ├── download_data.py          # Bulk data download
│   ├── update_universe.py        # Stock list updater
│   ├── clean_cache.py            # Cache cleanup
│   └── generate_report.py        # Report builder
│
├── logs/                          # Application logs
│   ├── app.log
│   ├── backtest.log
│   └── errors.log
│
└── output/                        # Generated outputs
    ├── recommendations/           # Daily recommendations
    │   └── YYYYMMDD_reco.csv
    ├── backtest/                  # Backtest results
    │   └── report_YYYYMMDD.json
    └── models/                    # Saved models
        ├── factor_v*.pkl
        └── model_v*.pkl
```

### Configuration Schemas

#### data_sources.yaml
```yaml
tcbs:
  base_url: "https://apipubaws.tcbs.com.vn"
  endpoints:
    historical: "/stock-insight/v2/stock/bars"
    intraday: "/stock-insight/v1/intraday"
    financial: "/financial-analysis/v1/finance"
  rate_limit:
    requests_per_second: 10
    burst: 20

vci:
  base_url: "https://api.vietcap.com.vn"
  endpoints:
    ohlcv: "/data/ohlcv"
    reports: "/data/financials"
  rate_limit:
    requests_per_second: 5
    burst: 10

cafef:
  base_url: "https://cafef.vn"
  scraper:
    delay_seconds: 1
    user_agent: "Mozilla/5.0"

universe:
  file: "data/list_stock.json"
  exchanges: ["HOSE", "HNX", "UPCOM"]
  min_liquidity: 1000000  # Minimum daily volume
```

#### rdagent_config.yaml
```yaml
scenarios:
  fin_quant:
    enabled: true
    iterations: 10
    action_selection: "bandit"  # bandit/llm/random

  fin_factor:
    enabled: true
    hypothesis_generation:
      max_factors: 50
      diversity_threshold: 0.7

  fin_model:
    enabled: true
    model_types: ["linear", "tree", "neural"]
    ensemble: true

llm:
  provider: "openai"  # openai/azure/litellm
  chat_model: "gpt-4-turbo"
  embedding_model: "text-embedding-3-small"
  temperature: 0.7
  max_tokens: 4096

docker:
  enabled: true
  timeout: 300  # seconds
  memory_limit: "4g"
```

#### qlib_config.yaml
```yaml
data:
  provider_uri: "data/processed/qlib_data"
  region: "vn"
  market: "vietnam"
  calendar: "vietnam_calendar.txt"
  instruments: "vietnam_instruments.txt"

features:
  fields: ["open", "close", "high", "low", "volume", "factor"]
  freq: "day"

model:
  task:
    model_type: "tabnet"  # lightgbm/xgboost/tabnet/lstm
    loss: "mse"

backtest:
  exchange:
    open_time: "09:00"
    close_time: "15:00"
    limit_threshold: 0.07  # 7% limit
  account:
    initial_cash: 1000000000  # 1B VND
    commission: 0.0015  # 0.15%
    tax: 0.001  # 0.1% sell tax
```

## Timeline Overview

- [ ] **Milestone 1**: Discovery & Setup (8 hours)
- [ ] **Milestone 2**: Data Ingestion (16 hours)
- [ ] **Milestone 3**: Preprocessing & Qlib Integration (12 hours)
- [ ] **Milestone 4**: RD-Agent Integration (20 hours)
- [ ] **Milestone 5**: Factor Engineering (16 hours)
- [ ] **Milestone 6**: Model Training & Backtest (20 hours)
- [ ] **Milestone 7**: Recommendation Generation (12 hours)
- [ ] **Milestone 8**: Testing & CI (16 hours)
- [ ] **Milestone 9**: Containerization & Docs (12 hours)
- [ ] **Milestone 10**: Demo & Delivery (8 hours)

**Total Estimated Time**: 140 hours (~3.5 weeks)

## Detailed Tasks

### Milestone 1: Discovery & Setup (8 hours)

**Goal**: Development environment ready with all dependencies installed and configured

#### Task 1.1: Create Project Structure (1 hour)
- [ ] Initialize git repository
- [ ] Create all directories as per structure
- [ ] Add .gitignore for Python, data files, logs
- [ ] Create empty __init__.py files
- **DoD**: All folders exist, git initialized

#### Task 1.2: Setup Development Environment (2 hours)
- [ ] Create Conda environment with Python 3.10
- [ ] Install core dependencies: rdagent, qlib, pandas, numpy
- [ ] Install ML libraries: scikit-learn, xgboost, lightgbm
- [ ] Install web/API tools: requests, beautifulsoup4, fastapi
- [ ] Test imports in Python REPL
- **DoD**: All packages import successfully

#### Task 1.3: Configure Environment Variables (1 hour)
- [ ] Create .env.example with all config keys
- [ ] Document each variable with comments
- [ ] Add OpenAI/Azure API key placeholders
- [ ] Set data paths and cache locations
- **DoD**: .env.example complete and documented

#### Task 1.4: Research RD-Agent Scenarios (2 hours)
- [ ] Clone RD-Agent repo and explore scenarios/qlib
- [ ] Understand fin_quant workflow and configuration
- [ ] Document hypothesis generation process
- [ ] Identify customization points for Vietnam data
- **DoD**: Clear understanding of RD-Agent flow

#### Task 1.5: Research Qlib Data Format (2 hours)
- [ ] Study Qlib data schema and binary format
- [ ] Understand factor field calculation
- [ ] Learn about calendar and instrument files
- [ ] Test dump_bin.py with sample data
- **DoD**: Can convert CSV to Qlib format

### Milestone 2: Data Ingestion (16 hours)

**Goal**: Reliable data fetching from all Vietnamese sources with caching

#### Task 2.1: Implement Base Adapter (2 hours)
- [ ] Create abstract BaseAdapter class
- [ ] Define common interface: fetch_ohlcv, fetch_fundamentals
- [ ] Implement retry logic with exponential backoff
- [ ] Add logging and error handling
- **DoD**: Base class with clear interface

#### Task 2.2: Implement TCBS Adapter (3 hours)
- [ ] Study TCBS API documentation
- [ ] Implement authentication if required
- [ ] Create fetch_historical_data method
- [ ] Create fetch_financial_reports method
- [ ] Handle pagination and date ranges
- **DoD**: Can fetch 1 year of data for 10 stocks

#### Task 2.3: Implement VCI Adapter (3 hours)
- [ ] Study VCI API documentation
- [ ] Implement API key authentication
- [ ] Create data fetching methods
- [ ] Map VCI fields to standard schema
- [ ] Test with multiple symbols
- **DoD**: Can fetch financial reports for all stocks

#### Task 2.4: Implement CafeF Scraper (3 hours)
- [ ] Analyze CafeF website structure
- [ ] Implement BeautifulSoup scraper
- [ ] Handle dynamic content if needed
- [ ] Create fallback to vnstock library
- [ ] Test scraping for 20 symbols
- **DoD**: Can scrape or fallback for all symbols

#### Task 2.5: Implement Rate Limiting (2 hours)
- [ ] Create RateLimiter class with token bucket
- [ ] Configure per-source limits
- [ ] Add request queuing
- [ ] Implement circuit breaker pattern
- **DoD**: No API blocks during bulk fetch

#### Task 2.6: Implement Caching Layer (2 hours)
- [ ] Create CacheManager with 24-hour TTL
- [ ] Use disk-based cache (pickle/parquet)
- [ ] Implement cache invalidation
- [ ] Add cache statistics logging
- **DoD**: Second fetch is 10x faster

#### Task 2.7: Data Validation (1 hour)
- [ ] Check for missing OHLCV data
- [ ] Validate price continuity
- [ ] Log data quality metrics
- [ ] Drop symbols with >20% missing data
- **DoD**: Quality report generated

### Milestone 3: Preprocessing & Qlib Integration (12 hours)

**Goal**: Clean, normalized data in Qlib binary format

#### Task 3.1: Implement Data Cleaner (2 hours)
- [ ] Handle missing values (forward fill, interpolation)
- [ ] Detect and handle outliers (IQR method)
- [ ] Remove duplicate entries
- [ ] Validate OHLCV relationships (High >= Low, etc.)
- **DoD**: No data anomalies in output

#### Task 3.2: Implement Timezone Converter (1 hour)
- [ ] Convert all timestamps from UTC+7 to UTC
- [ ] Handle daylight saving if applicable
- [ ] Ensure date alignment across sources
- **DoD**: All dates in UTC format

#### Task 3.3: Implement Price Adjuster (2 hours)
- [ ] Calculate adjustment factors from splits/dividends
- [ ] Apply adjustments to OHLCV
- [ ] Ensure price continuity
- [ ] Create factor field (adjusted/original)
- **DoD**: Adjusted prices are continuous

#### Task 3.4: Implement Qlib Formatter (3 hours)
- [ ] Create CSV files in Qlib format
- [ ] Generate calendar file for Vietnam market
- [ ] Generate instruments file with metadata
- [ ] Run dump_bin.py to create binary data
- **DoD**: Qlib can load the data

#### Task 3.5: Create Feature Engineer (2 hours)
- [ ] Add basic technical indicators (SMA, EMA)
- [ ] Calculate returns (1d, 5d, 20d)
- [ ] Add volume indicators (VWAP, OBV)
- [ ] Create volatility measures
- **DoD**: 20+ features per stock

#### Task 3.6: Integration Tests (2 hours)
- [ ] Test full pipeline: ingest → clean → format
- [ ] Verify data consistency across sources
- [ ] Check Qlib data loading
- [ ] Benchmark performance (time per stock)
- **DoD**: Process 100 stocks in <10 minutes

### Milestone 4: RD-Agent Integration (20 hours)

**Goal**: RD-Agent generating hypotheses and experiments for Vietnam market

#### Task 4.1: Create Vietnam Data Adapter (4 hours)
- [ ] Subclass RD-Agent data interface
- [ ] Map Qlib data to RD-Agent format
- [ ] Handle market-specific fields
- [ ] Test data loading in RD-Agent
- **DoD**: RD-Agent reads local Vietnam data

#### Task 4.2: Configure LLM Backend (2 hours)
- [ ] Set up OpenAI API credentials
- [ ] Configure model selection (GPT-4)
- [ ] Set temperature and token limits
- [ ] Test LLM connectivity
- **DoD**: LLM responds to test prompts

#### Task 4.3: Implement Hypothesis Generator (4 hours)
- [ ] Create prompts for Vietnam market context
- [ ] Generate factor hypotheses
- [ ] Generate model hypotheses
- [ ] Store hypotheses with metadata
- **DoD**: 10 unique hypotheses generated

#### Task 4.4: Implement Experiment Runner (4 hours)
- [ ] Create experiment configuration
- [ ] Run factor experiments
- [ ] Run model experiments
- [ ] Collect experiment results
- **DoD**: 1 complete experiment cycle

#### Task 4.5: Implement Results Summarizer (3 hours)
- [ ] Parse experiment outputs
- [ ] Calculate success metrics
- [ ] Rank hypotheses by performance
- [ ] Generate summary reports
- **DoD**: Readable experiment reports

#### Task 4.6: Create Feedback Loop (3 hours)
- [ ] Feed results back to hypothesis generation
- [ ] Implement evolutionary selection
- [ ] Track hypothesis lineage
- [ ] Monitor convergence
- **DoD**: Second iteration improves on first

### Milestone 5: Factor Engineering (16 hours)

**Goal**: Comprehensive factor library combining classical and AI-generated factors

#### Task 5.1: Implement Classical Factors (4 hours)
- [ ] Momentum: returns, moving averages, RSI
- [ ] Value: P/E, P/B, dividend yield
- [ ] Volatility: standard deviation, beta, VIX
- [ ] Volume: turnover, Amihud illiquidity
- [ ] Quality: ROE, ROA, debt ratios
- **DoD**: 30+ classical factors

#### Task 5.2: Implement Technical Factors (3 hours)
- [ ] MACD and signal lines
- [ ] Bollinger Bands
- [ ] Stochastic oscillator
- [ ] Fibonacci retracements
- [ ] Pattern recognition (head-shoulders, triangles)
- **DoD**: 15+ technical factors

#### Task 5.3: Implement TCBS Fundamental Factors (3 hours)
- [ ] Extract quarterly financial data
- [ ] Calculate growth rates (revenue, earnings)
- [ ] Compute efficiency ratios
- [ ] Industry-relative metrics
- **DoD**: 20+ fundamental factors

#### Task 5.4: Integrate RD-Agent Factors (3 hours)
- [ ] Parse factor suggestions from RD-Agent
- [ ] Implement suggested formulas
- [ ] Validate factor calculations
- [ ] Add to factor registry
- **DoD**: 10+ AI factors integrated

#### Task 5.5: Create Factor Registry (2 hours)
- [ ] Design factor metadata schema
- [ ] Implement factor versioning
- [ ] Create factor dependency graph
- [ ] Add factor importance tracking
- **DoD**: All factors catalogued

#### Task 5.6: Factor Quality Control (1 hour)
- [ ] Check factor correlations
- [ ] Identify redundant factors
- [ ] Validate factor stability
- [ ] Generate factor statistics
- **DoD**: Factor quality report

### Milestone 6: Model Training & Backtest (20 hours)

**Goal**: Trained models with validated backtest performance

#### Task 6.1: Implement Model Trainer (4 hours)
- [ ] Create training pipeline
- [ ] Implement cross-validation
- [ ] Add early stopping
- [ ] Save model checkpoints
- **DoD**: Can train XGBoost model

#### Task 6.2: Implement Model Types (6 hours)
- [ ] Linear: Ridge, Lasso, ElasticNet
- [ ] Tree: XGBoost, LightGBM, CatBoost
- [ ] Neural: MLP, LSTM, Transformer
- [ ] Ensemble: Voting, stacking
- **DoD**: All model types working

#### Task 6.3: Implement Hyperparameter Optimization (3 hours)
- [ ] Set up Optuna for tuning
- [ ] Define search spaces
- [ ] Implement objective functions
- [ ] Save best parameters
- **DoD**: 20% performance improvement

#### Task 6.4: Implement Backtest Runner (4 hours)
- [ ] Set up Qlib backtest engine
- [ ] Configure Vietnam market rules
- [ ] Implement position sizing
- [ ] Add transaction costs
- **DoD**: Backtest runs for 2015-2024

#### Task 6.5: Implement Metrics Calculation (2 hours)
- [ ] Annual return (ARR)
- [ ] Sharpe ratio
- [ ] Maximum drawdown
- [ ] Turnover rate
- [ ] Win rate and profit factor
- **DoD**: All metrics computed

#### Task 6.6: Create Model Registry (1 hour)
- [ ] Version models with timestamps
- [ ] Store model metadata
- [ ] Track performance history
- [ ] Implement model comparison
- **DoD**: Model versioning working

### Milestone 7: Recommendation Generation (12 hours)

**Goal**: Daily stock recommendations with explainability

#### Task 7.1: Implement Recommendation Generator (3 hours)
- [ ] Load latest model predictions
- [ ] Apply portfolio constraints
- [ ] Generate buy/sell/hold signals
- [ ] Calculate position sizes
- **DoD**: Recommendations for all stocks

#### Task 7.2: Implement Stock Ranker (2 hours)
- [ ] Combine multiple model scores
- [ ] Apply sector neutralization
- [ ] Rank by expected returns
- [ ] Filter by liquidity
- **DoD**: Top 20 stocks selected

#### Task 7.3: Implement Explainer (3 hours)
- [ ] Add SHAP for feature importance
- [ ] Generate factor attributions
- [ ] Create confidence scores
- [ ] Write explanation text
- **DoD**: Each recommendation explained

#### Task 7.4: Create Output Formatter (2 hours)
- [ ] Generate CSV with required columns
- [ ] Create JSON report with metrics
- [ ] Format for readability
- [ ] Add metadata and timestamps
- **DoD**: Professional output format

#### Task 7.5: Create CLI Interface (2 hours)
- [ ] Implement main command: run-pipeline
- [ ] Add date parameter
- [ ] Add dry-run mode
- [ ] Add verbose logging option
- **DoD**: CLI works end-to-end

### Milestone 8: Testing & CI (16 hours)

**Goal**: Comprehensive test coverage with CI/CD pipeline

#### Task 8.1: Write Unit Tests - Ingestion (3 hours)
- [ ] Test each adapter separately
- [ ] Mock API responses
- [ ] Test error handling
- [ ] Test rate limiting
- **DoD**: 100% coverage for ingest/

#### Task 8.2: Write Unit Tests - Preprocessing (2 hours)
- [ ] Test data cleaning
- [ ] Test timezone conversion
- [ ] Test Qlib formatting
- [ ] Test feature engineering
- **DoD**: 100% coverage for preprocessing/

#### Task 8.3: Write Unit Tests - Factors (2 hours)
- [ ] Test factor calculations
- [ ] Validate factor ranges
- [ ] Test with edge cases
- **DoD**: All factors tested

#### Task 8.4: Write Unit Tests - Models (2 hours)
- [ ] Test model training
- [ ] Test predictions
- [ ] Test model saving/loading
- **DoD**: All models tested

#### Task 8.5: Write Integration Tests (3 hours)
- [ ] Test full pipeline on sample data
- [ ] Test error recovery
- [ ] Test performance benchmarks
- **DoD**: End-to-end test passes

#### Task 8.6: Setup GitHub Actions (2 hours)
- [ ] Create test workflow
- [ ] Add linting (flake8, black)
- [ ] Add type checking (mypy)
- [ ] Add coverage reporting
- **DoD**: Green CI badge

#### Task 8.7: Create Test Fixtures (2 hours)
- [ ] Generate sample data for 10 stocks
- [ ] Create mock API responses
- [ ] Build test factor data
- [ ] Prepare expected outputs
- **DoD**: Tests run offline

### Milestone 9: Containerization & Documentation (12 hours)

**Goal**: Fully containerized application with comprehensive documentation

#### Task 9.1: Create Dockerfile (2 hours)
- [ ] Use Python 3.10 base image
- [ ] Install system dependencies
- [ ] Copy and install Python packages
- [ ] Set up entrypoint
- **DoD**: Docker build succeeds

#### Task 9.2: Create docker-compose.yml (2 hours)
- [ ] Define main service
- [ ] Add volume mounts for data
- [ ] Configure environment variables
- [ ] Add health checks
- **DoD**: docker-compose up works

#### Task 9.3: Create Makefile (1 hour)
- [ ] Add setup target
- [ ] Add run-demo target
- [ ] Add test target
- [ ] Add clean target
- **DoD**: Make commands work

#### Task 9.4: Write README.md (3 hours)
- [ ] Project overview
- [ ] Installation instructions
- [ ] Usage examples
- [ ] API documentation
- [ ] Troubleshooting guide
- **DoD**: New user can run pipeline

#### Task 9.5: Write Architecture Docs (2 hours)
- [ ] System design document
- [ ] Data flow diagrams
- [ ] Component descriptions
- [ ] Configuration guide
- **DoD**: Architecture clear to developers

#### Task 9.6: Create API Documentation (2 hours)
- [ ] Document REST endpoints
- [ ] Provide curl examples
- [ ] Create Postman collection
- [ ] Add OpenAPI spec
- **DoD**: API fully documented

### Milestone 10: Demo & Delivery (8 hours)

**Goal**: Working demonstration and clean handover

#### Task 10.1: Create Demo Notebook (3 hours)
- [ ] Load sample data
- [ ] Show data preprocessing
- [ ] Demonstrate factor generation
- [ ] Run backtest
- [ ] Generate recommendations
- **DoD**: Notebook runs without errors

#### Task 10.2: Prepare Demo Data (1 hour)
- [ ] Select 10 representative stocks
- [ ] Get 1 year of historical data
- [ ] Include various sectors
- [ ] Ensure data quality
- **DoD**: Demo data ready

#### Task 10.3: Run Acceptance Tests (2 hours)
- [ ] Full pipeline on demo data
- [ ] Verify output formats
- [ ] Check performance metrics
- [ ] Validate recommendations
- **DoD**: All acceptance criteria met

#### Task 10.4: Final Review (2 hours)
- [ ] Code review and cleanup
- [ ] Update all documentation
- [ ] Remove debug code
- [ ] Check for secrets in code
- [ ] Final commit with tags
- **DoD**: Production-ready code

## Assumptions & Decisions

### Data Sources
1. **TCBS API**: Primary source for OHLCV and financial data
2. **VCI API**: Secondary source for validation and additional metrics
3. **CafeF**: Web scraping with vnstock as fallback
4. **Missing Data**: Forward fill for up to 5 days, then drop symbol

### Model Configuration
1. **Training Period**: 2015-2022 (8 years)
2. **Testing Period**: 2023-2024 (2 years)
3. **Retraining**: Monthly with expanding window
4. **Model Selection**: Ensemble of top 3 performers

### Technical Decisions
1. **Python Version**: 3.10 for compatibility
2. **LLM Provider**: OpenAI GPT-4 (fallback to GPT-3.5)
3. **Data Storage**: Parquet for raw, Qlib binary for processed
4. **Cache Duration**: 24 hours for API responses

### Business Rules
1. **Universe**: All stocks with >1M VND daily volume
2. **Position Limits**: Max 5% per stock, 20 stocks total
3. **Risk Controls**: 7% daily limit (Vietnam market)
4. **No Auto-Trading**: Manual execution only

## Risk Mitigation

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| API Rate Limits | High | Implement caching, queuing, and circuit breakers |
| CafeF Scraping Fails | Medium | Use vnstock library as fallback |
| RD-Agent Adaptation | High | Start with simple scenarios, iterate |
| Qlib Format Issues | Medium | Extensive data validation and testing |
| Model Overfitting | High | Robust cross-validation, regularization |

### Data Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing Historical Data | High | Multiple sources, interpolation |
| Data Quality Issues | High | Validation checks, outlier detection |
| Corporate Actions | Medium | Adjustment factors, manual review |
| Market Hours Changes | Low | Configurable trading calendar |

### Operational Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM API Costs | Medium | Token limits, caching, monitoring |
| Compute Resources | Medium | Optimize code, use cloud if needed |
| Model Drift | High | Daily monitoring, monthly retraining |
| Documentation Lag | Low | Update docs with code changes |

## Success Metrics

1. **Data Coverage**: >90% of 735 stocks with complete data
2. **Pipeline Performance**: <30 minutes for daily run
3. **Model Performance**: Sharpe >1.5, ARR >20%
4. **Code Quality**: >80% test coverage, <5% tech debt
5. **Documentation**: 100% API coverage, clear README

## Next Steps

After implementation:
1. **Performance Optimization**: Profile and optimize bottlenecks
2. **Feature Expansion**: Add more data sources (news, social)
3. **Model Enhancement**: Experiment with advanced architectures
4. **UI Development**: Build web dashboard for visualizations
5. **Production Deployment**: Cloud infrastructure setup

## Appendices

### A. Sample Configuration Files

See configuration schemas in Architecture Design section.

### B. API Response Examples

```json
// TCBS OHLCV Response
{
  "data": [
    {
      "tradingDate": "2024-01-15",
      "open": 45000,
      "high": 46000,
      "low": 44500,
      "close": 45500,
      "volume": 1500000
    }
  ]
}

// Recommendation Output
{
  "date": "2025-01-15",
  "recommendations": [
    {
      "symbol": "VNM",
      "action": "BUY",
      "weight": 0.05,
      "confidence": 0.85,
      "top_factors": ["momentum_20d", "pe_ratio", "volume_surge"],
      "explanation": "Strong momentum with improving fundamentals"
    }
  ],
  "metrics": {
    "expected_return": 0.15,
    "risk_score": 0.3,
    "sharpe_ratio": 1.8
  }
}
```

### C. Command Examples

```bash
# Setup environment
make setup

# Run full pipeline
python cli.py run-pipeline --date 2025-01-15

# Run with specific config
python cli.py run-pipeline --config config/production.yaml

# Generate only recommendations
python cli.py generate-recommendations --model models/latest.pkl

# Run backtest only
python cli.py backtest --start 2023-01-01 --end 2024-12-31

# Update stock universe
python scripts/update_universe.py --exchange HOSE

# API server
python -m uvicorn api.server:app --reload
```

---

*This implementation plan provides a comprehensive roadmap for building the RD-Agent Vietnam Stock Pipeline. Each milestone is designed to be independently valuable while contributing to the complete system.*