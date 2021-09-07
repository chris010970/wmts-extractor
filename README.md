# TLDR
Extract tiles from OGC WMTS end points collocated with annotated areas of interest and reassemble into a mosaicked georeferenced image

# Overview
This software implements functionality to query Digital Globe catalogue and facilitate download of Maxar satellite imagery satisfying user-defined spatial and temporal constraints via cost and bandwidth-efficient WMTS end point. 

The software utilises a series of standard OGC WFS requests to retrieve metadata of imagery aligned with area of interest – point, line and polygon geometries are supported – in any OGR supported file format – see: https://gdal.org/drivers/vector/index.html. Additional filter parameters may also be specified by the end user based on acquisition date, product type, cloud cover, etc. Response from Digital Globe WFS end point is subsequently parsed to retrieve unique feature identifier of images satisfying user-defined constraints.

For each image identified for download, the software subsequently forwards a series of WMTS requests – with unique feature identifier appended to URI – to download each PNG / JPG 256x256 tile aligned with nominated area of interest. Having completed downloads, individual tiles are assimilated into a single georeferenced image and copied into datetime indexed directory on local file system.

Additionally, this software tool also provides integrated support for sourcing and downloading imagery via additional WMTS end points – currently, time series Sentinel-1/2 imagery via Sentinel-Hub and selected base map layers via ESRI MapServer services.

# Configuration

The software has been developed as a Python module – it requires following dependencies - GDAL, Shapely, pyCURL, pyProj.  When running under Windows OS, these libraries may be downloaded as wheel packages from the following location: https://www.lfd.uci.edu/~gohlke/pythonlibs/. 

From a command prompt window, the software is executed with the following command line arguments:
> _run.py <pathname-to-config-file> <zoom-level> <output-path> [options]_

### Argument 1: Configuration File
The <pathname-to-config-file> argument is full pathname of a YAML configuration file specific to this software application. The YAML configuration file specifies identity of WMTS end point along with necessary login credentials. It also defines full pathname to OGR-supported file defining one or more area of interest geometries. Example configuration files may be found in the [cfg sub-directory](https://github.com/chris010970/wmts-extractor/tree/main/cfg) of this repository.
  
To create a configuration file for a specific end user, the following fields should be updated:
* credentials:
  * username: user id (typically email address)
  * password: service password
* uri:
  * id: optional 32-character api id 

To download imagery aligned with an area of interest, the following fields should be updated:
* aoi
  * pathname: full pathname to OGR supported file encoding one or more Point, Line or Polygon geometries
  * field: [optional] data attribute uniquely identifying each geometry feature in nominated AOI file – for example: osm_id. Attribute value is appended to output filename / output directory structure – defaults to {GeometryType}_{Index} 
  * buffer: Buffering distance in metres added to AOI geometry – for point geometries, buffer distance is utilised to create bounding box centred on nominated point location 

### Argument 2: Zoom Level
The <zoom-level> argument stipulates an integer value between 1 and maximum zoom level supported by WMTS end point. For SecureWatch WMTS end point, maximum zoom level is generally 20. Compromise exists between spatial resolution of output imagery and bandwidth / cost overhead of streaming data from denser WMTS tile pyramids.

### Argument 3: Output Path
The <output-path> specifies root directory to copy output images – software application creates the following sub-directory hierarchy to store output images:
 
### Optional Arguments
List of current command line options supported by the software application:
* -s, --start_datetime: 
  * _Ignore imagery acquired before start datetime – format DD/MM/YYYY HH:MM:SS_
* -e, --end_datetime: 
  * _Ignore imagery acquired after end datetime – format DD/MM/YYYY HH:MM:SS_
*	-f, --features:
  * _Identify imagery for download by specifying list of space-separated, unique feature identifiers defined in metadata_
* --overwrite:
  * _Overwrite existing output files – otherwise skip download_
* --info_only:
  * _Print table of metadata field values for imagery satisfying user-defined spatial and temporal constraints_

### Typical Usage
* Download all available imagery from zoom level 19 tile pyramid hosted by SecureWatch WMTS end point and copy output imagery into sub-directories below Desktop\Images
> _python run.py c:\..\Desktop\cfg\securewatch.yml 19 c:\..\Desktop\images\_
* Download all available zoom level 18 imagery for 2018 from SecureWatch WMTS end point and copy output imagery into sub-directories below Desktop\Images
> _python run.py c:\..\Desktop\cfg\securewatch.yml 18 c:\..\Desktop\images\ -s 01/01/2018 00:00:00 -e 31/12/2018 23:59:59_
* Retrieve metadata of available zoom level 17 imagery for 2019 and display on command line:
> _python run.py c:\..\Desktop\cfg\securewatch.yml 17 c:\..\Desktop\images\ -s 01/01/2019 00:00:00 -e 31/12/2019 23:59:59 –info_only_
