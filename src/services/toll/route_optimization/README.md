# Route Optimization System - Architecture & Steps

## Overview

This module provides a modular system for route optimization with toll detection and analysis using spatial indexing and precise distance calculations.

## Architecture

### Folder Structure

```
src/services/toll/route_optimization/
├── main/
│   └── intelligent_optimizer.py    # Main orchestrator
├── route_handling/
│   ├── base_route_provider.py      # Route data extraction
│   └── tollway_processor.py        # Tollway-specific processing
├── toll_analysis/
│   ├── toll_identifier.py          # Main toll detection orchestrator
│   ├── toll_selector.py            # Toll selection logic
│   ├── spatial/
│   │   └── spatial_index.py        # Rtree-based spatial indexing
│   └── detection/
│       ├── distance_calculator.py  # Optimized distance calculations
│       └── toll_classifier.py      # Toll classification and mapping
├── segmentation/
│   ├── segment_creator.py          # Route segment creation
│   └── segment_calculator.py       # Segment cost calculations
├── assembly/
│   └── route_assembler.py          # Final route assembly
└── utils/
    ├── cache_accessor.py           # Cache data access
    ├── distance_calculator.py      # General distance utilities
    └── route_extractor.py          # Route data extraction
```

## Processing Pipeline (8 Steps)

### Step 1: Route Data Extraction
**Module**: `route_handling/base_route_provider.py`
- Extracts route coordinates from ORS route data
- Validates route structure and format

### Step 2: Tollway Processing
**Module**: `route_handling/tollway_processor.py`
- Processes tollway-specific route segments
- Prepares route data for toll analysis

### Step 3: Toll Detection & Analysis
**Main Module**: `toll_analysis/toll_identifier.py`

4-phase detection pipeline:
- **Phase 1**: Spatial prefiltering (`spatial/spatial_index.py`)
- **Phase 2**: Distance calculation (`detection/distance_calculator.py`)
- **Phase 3**: Classification & mapping (`detection/toll_classifier.py`)
- **Phase 4**: Shapely verification (`verification/shapely_verifier.py`)

### Step 4: Toll Selection
**Module**: `toll_analysis/toll_selector.py`
- ✅ **Completed**: Selection by count with removal from end logic
- ✅ **System constraints**: Open/closed system validation
- ✅ **Optimization**: Automatic replacement of removed closed tolls
- ⏳ **Budget selection**: Left empty for future implementation

### Step 5: Segment Creation  
**Module**: `segmentation/segment_creator.py`
- Status: Awaiting specification

### Step 6: Segment Calculation
**Module**: `segmentation/segment_calculator.py`  
- Status: Awaiting specification

### Step 7: Cache Integration
**Module**: `utils/cache_accessor.py`
- Provides access to cached OSM and toll data

### Step 8: Route Assembly
**Module**: `assembly/route_assembler.py`
- Assembles final optimized route with toll information
