# Cobalt Heatmap

### Goal:

*Identify areas where cobalt is likely to appear based on the presence of serpentinite and granodiorite*

### Steps to Success:
- Classified locations as containing either serpentinite, granodiorite, or None
- Identified locations where both serpentinite and granodiorite are said to appear
- Created a planar graph of all intersections
- Calculated probabilities of cobalt being found based on the presence of both serpentinite and granodiorite
- Plotted heatmap showing probabilities of finding cobalt within each location

### To run:
**Be sure to have python v3.0 or higher installed**

1) Start by setting up env
`pip install -r requirements.txt`

2) Then run
`python3 bedrock_heatmap.py --buffer [buffer_parameter]`

*Note: if no buffer parameter is passed, default will be `5km`*
**Map saved as cobalt.jpg**

### Data:
`BedrockHeatMap` class contains the following properties:
```
BHM = BedrockHeatMap()

# original dataset with classification value
BHM.data

# areas where cobalt is predicted to reside
BHM.possible_cobalt_deposits

# original dataset with classification, cobalt deposit locations, and probability of finding cobalt
BHM.cobalt
```