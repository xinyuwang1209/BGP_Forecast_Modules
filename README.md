# BGP_Forecast_Modules

## Installation
* Use pip
``` pip install BGP_Forecast_Modules
```
* or clone from GitHub
``` git clone https://github.com/xinyuwang1209/BGP_Forecast_Modules
    cd https://github.com/xinyuwang1209/BGP_Forecast_Modules
    pip install -r requirements.txt --user
    python setup.py install --user
```

## Usage
### Get config file, update parameters, set to BGP_Forecast_Modules
``` from BGP_Forecast_Modules import *
    Instance = BGP_Forecast_Modules()
    # Get config
    config = Instance.get_config()
    # Make some modification on config file here
    # Set config
    Instance.set_config()
    # Reset config to default
    Instance.reset_config_default()
```

### Run ROAs_Collector
``` from BGP_Forecast_Modules import *
    Instance = BGP_Forecast_Modules()
    Instance.run_ROAs_Collector()
```

### Run MRT_Collector, Hijack_Collector, and AS_Relationship_Collector
* Not completed.
``` from BGP_Forecast_Modules import *
    Instance = BGP_Forecast_Modules()
    Instance.run_MRT_Collector()
    Instance.run_Hijack_Collector()
    Instance.run_AS_Relationship_Collector()
```

### Run PyBGPExtrapolator
* Not completed.
``` from BGP_Forecast_Modules import *
    Instance = BGP_Forecast_Modules()
    Instance.run_PyBGPExtrapolator()
```

### Run What_If_Analysis_Evaluator
* Not completed.
``` from BGP_Forecast_Modules import *
    Instance = BGP_Forecast_Modules()
    Instance.What_If_Analysis_Evaluator()
```

### A full run of BGP_Forecast_Serive
* Not completed.
``` from BGP_Forecast_Modules import *
    Instance = BGP_Forecast_Modules()
    Instance.run_ROAs_Collector()
    Instance.run_MRT_Collector()
    Instance.run_Hijack_Collector()
    Instance.run_AS_Relationship_Collector()
    Instance.run_PyBGPExtrapolator()
    Instance.What_If_Analysis_Evaluator()
```



## Configuration specification
### Database Schema:

#### roas Schema
* This data comes from the RIPE rpki-validator-3 and is retrieved by the ROAs_Collector module (ROAs_Collector.py)
* roa_id: id of roa in table (primary key)
* roa_prefix: prefix (inet)
* roa_asn: ASN (bigint)
* roa_max_length: max length specified by prefix (integer)
* Create Table SQL commands:
    ```sql
    CREATE TABLE roas (
        roa_id serial PRIMARY KEY,
        roa_asn bigint,
        roa_prefix inet,
        roa_max_length integer
    );
    ```
(Optional:
        roa_created_at TIMESTAMP DEFAULT now() NOT NULL,
        roa_updated_at TIMESTAMP DEFAULT now() NOT NULL
)

#### prefix_origin Schema
* This data comes from RIPE rpki-validator-3 retrieved by the Conflicted_Identifier module (Conflicted_Identifier.py)
* po_id: id of prefix_origin table (primary key)
* prefix: prefix (inet)
* orign: ASN (bigint)
* alter_as: whether there exists a best alternative announcement (boolean)
* validity: type of validity (boolean)
    * true ('INVALID_ASN'), false ('INVALID_LENGTH')
* hijack: whether there exists a suspected attack event (boolean)
* policyid: id of applied policy
* decision_1: decision made by the policy 1 (smallint)
* decision_2: decision made by the policy 2 (smallint)
* ...
  * 0 (enforce), 1 (deprefer), 2 (pass), 3 (whitelist)
* time: time_record of the announcement
* Create Table SQL commands:
    ```sql
    CREATE TABLE prefix_origin (
        po_id serial PRIMARY KEY,
        prefix inet,
        origin bigint,
        validity smallint,
        hijack boolean,
        policyid smallint,
        decision smallint,
        next_hop bigint,
        as_path bigint ARRAY,
        time integer
    );
    ```

#### unique_prefix_origin Schema
* upo_id: id of unique_prefix_origin table (primary key)
* prefix: prefix (cidr)
  * We decide to move from inet to cidr because inet ignores the mask when the length = 32 (in IPv4)
* origin: AS number (bigint)
* invalid_length: (boolean)
* invalid_length: (boolean)
* hijack: whether there exists a suspected attack event (boolean)
* policyid: id of applied policy
* decision: decision made by the policy (smallint)
  * 0 (enforce), 1 (deprefer), 2 (pass), 3 (whitelist)
* as_path: path of the announcement
* time: time_record of the announcement
* Create Table SQL commands:
    ```sql
    CREATE TABLE unique_prefix_origin (
        upo_id serial PRIMARY KEY,
        prefix cidr,
        origin bigint,
        invalid_length boolean default true,
        invalid_asn boolean default true,
        hijack boolean,
        decision smallint,
        next_hop bigint,
        time integer
    );
    ```

#### unique_prefix_origin_wroa Schema
* upow_id: id of unique_prefix_origin_wroa table (primary key)
* prefix: prefix (cidr)
* origin: AS number (bigint)
* invalid_length: (boolean)
* invalid_length: (boolean)
* hijack: whether there exists a suspected attack event (boolean)
* policyid: id of applied policy
* decision: decision made by the policy (smallint)
  * 0 (enforce), 1 (deprefer), 2 (pass), 3 (whitelist)
* as_path: path of the announcement
* time: time_record of the announcement
* Create Table SQL commands:
    ```sql
    CREATE TABLE unique_prefix_origin (
        upo_id serial PRIMARY KEY,
        prefix cidr,
        origin bigint,
        invalid_length boolean default true,
        invalid_asn boolean default true,
        hijack boolean,
        decision smallint,
        next_hop bigint,
        time integer
    );
    ```



#### what_if_analysis Schema
* This data is retrieved by the Conflict_Identifier (Conflicted_Identifier.py and Whatif_Analysis.py)
* wia_id : id of what_if analysis table (primary key)
* hijack: the total number of announcements with suspected attack records (labeled as "real conflicted announcements")
* n_true_positive: the total number of real conflicted announcements enforced or preferred
    * n_true-positive rate can be calculated by ```math$`\frac{wi\_true_positive}{(wi\_invalid -  wi\_attack/)} `$```
* n_false_positive: total number of non-real conflicted announcements enforeced or deprefered
    * n_false-positive rate can be calculated by $`\frac{wi\_false\_positive}{(wi\_invalid -  wi\_attack/)}`$
* n_true_negative: total number of real conflicted announcements passed or whitelisted
    * n_true_negative rate can be calculated by $`\frac{wi\_true\_negative}{wi\_attack}`$
* n_false_negative: total number of non-real conflicted announcements passed or whitelisted
    * n_false_negative rate can be calculated by $`\frac{wi\_false\_negative}{wi\_attack}`$
  * Create Table SQL commands:
    ```sql
    CREATE TABLE what_if_analysis (
        wia_id serial PRIMARY KEY,
        asn bigint,
        n_anno integer,
        n_invalid integer,
        n_hijack integer,
        n_true_positive integer,
        n_false_positive integer,
        n_true_negative integer,
        n_false_negative integer
    );
    ```
## Q&A
### PostgreSQL Database Related questions
#### Why is prefix defined in cidr instead inet?
* In IPv4, if the mask of a prefix is 32, inet format will ignore its mask which makes ipaddress and other python libraries not recognize it correctly.
