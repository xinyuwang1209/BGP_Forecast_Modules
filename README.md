# BGP_Forecast_Modules

## Usage
``` git clone https://github.com/xinyuwang1209/BGP_Forecast_Modules
    cd https://github.com/xinyuwang1209/BGP_Forecast_Modules
    pip install -r requirements.txt --user
    python setup.py install --user
```

## Get config file, update parameters, set to BGP_Forecast_Modules
``` from BGP_Forecast_Modules import *
    Instance = BGP_Forecast_Modules()
    Instance.run_ROAs_Collector()
```

## Run ROAs_Collector
``` from BGP_Forecast_Modules import *
    Instance = BGP_Forecast_Modules()
    Instance.run_ROAs_Collector()
```

## Run MRT_Collector, Hijack_Collector, and AS_Relationship_Collector
* Not completed.
``` from BGP_Forecast_Modules import *
    Instance = BGP_Forecast_Modules()
    Instance.run_MRT_Collector()
    Instance.run_Hijack_Collector()
    Instance.run_AS_Relationship_Collector()
```

## Run PyBGPExtrapolator
* Not completed.
``` from BGP_Forecast_Modules import *
    Instance = BGP_Forecast_Modules()
    Instance.run_ROAs_Collector()
```
