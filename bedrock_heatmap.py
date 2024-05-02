import time
from itertools import combinations

import click
import pandas as pd
import geoplot as gplt
import geopandas as gpd
import matplotlib.pyplot as plt

from shapely.ops import unary_union, polygonize, cascaded_union
from shapely.geometry import LineString, MultiLineString, Polygon, MultiPolygon, LinearRing

class BedrockHeatMap:
    CLASSIFICATIONS = ["S", "G"]
    
    def __init__(self, buffer: float, file_name: str="data/BedrockP.shp"):
        self.buffer = buffer
        self.data =  self._data(file_name)
        self.conditional = self._conditions()
        self.boundary = gpd.GeoSeries(LineString(unary_union(self.data["geometry"]).exterior))
    
    def _data(self, file: str) -> gpd.GeoDataFrame: 
        df = gpd.read_file(file)
        df["class"] = df.apply(self._classify, axis=1)
        return df
    
    def _conditions(self) -> gpd.GeoDataFrame:
        """
        Returns dataframe of locations with serpentinite or granodiorite
        """
        df = self.data
        return df[df["class"].isin(self.CLASSIFICATIONS)]

    def _classify(self, row) -> str or None: # TODO: classify bedrock locations using strat units/name/age
        """
        Returns classification of bedrock for a given location
        """
        serpentinite_keywords = ["serpentinite", "ultramafic"]
        granodiorite_keywords = ["granodiorite", "volcanic"]
    
        if row["strat_name"] is None:
            return
        if any(keyword in row["strat_name"].lower() for keyword in serpentinite_keywords):
            return self.CLASSIFICATIONS[0]
        if (
            any(keyword in row["strat_name"].lower() for keyword in granodiorite_keywords)
            or row["strat_age"].lower() == "lower cretaceous"
        ):
            return self.CLASSIFICATIONS[1]
        return
    
    def _cobalt_deposits(self, row) -> gpd.GeoSeries:
        """
        Returns all cobalt deposits for a given location
        """
        cobalt_deposits = []
        for deposit in self.possible_cobalt_deposits:
            if row["geometry"].intersects(deposit):
                cobalt_deposits.append(deposit)
        return cobalt_deposits
    
    def _probability(self, row) -> float:
        """
        Returns probabilty of finding cobalt deposit for a given location
        """
        
        # apply Bayes Theorem
        total_land_area = pd.Series(self.data["area_m2"]).sum()
        
        # P(C): probability of cobalt
        cobalt_area = sum(cobalt.area for cobalt in row["cobalt_deposits"])
        cobalt_prob =  cobalt_area / row["area_m2"] # getting really large number here, finding that cobalt areas are larger than location area
        
        # P(S+G|C): probability of serp and gran resulting in cobalt
        cobalt_deposits_area = pd.Series(self.possible_cobalt_deposits.area).sum()
        cobalt_deposits_prob = cobalt_deposits_area / total_land_area
        
        # P(S+G): probability of finding serp or gran
        df_area = pd.Series(self.conditional["area_m2"]).sum()
        df_prob = df_area / total_land_area
        
        # P(C|S+G) = P(C)P(S+G|C)/P(S+G)
        probability = (cobalt_prob * cobalt_deposits_prob) / df_prob
        return round(probability, 2)
    
    @property
    def possible_cobalt_deposits(self) -> gpd.GeoSeries:
        """
        Returns a planar graph of intersecting polygons of possible cobalt deposits
        """
        
        # find intersections of serpentinite and granodiorite
        intersections = [
            polygon_1.intersection(polygon_2)
            for polygon_1, polygon_2 in combinations(self.conditional["geometry"], 2)
            if polygon_1.intersects(polygon_2)
        ]
        
        # cut lines at each intersection
        rings = [] # collection of LineStrings
        for intersection in intersections:
            
            # get list of LineStrings from Polygons
            if isinstance(intersection, Polygon):
                rings.extend([LineString(list(intersection.exterior.coords))])
    
            # get list of LineStrings from MultiLineString
            elif isinstance(intersection, MultiLineString):
                rings.extend([linestring for linestring in intersection])
        
        # create union of rings and polygonize
        union = unary_union(rings)
        polygons = [Polygon(geom.buffer(self.buffer).exterior) for geom in polygonize(union)]
        return gpd.GeoSeries(polygons)

    @property
    def cobalt(self) -> gpd.GeoDataFrame:
        """
        Returns dataframe with probabilities of finding cobalt
        """
        df = self.data
        df["cobalt_deposits"] = df.apply(self._cobalt_deposits, axis=1)
        df["probability"] = df.apply(self._probability, axis=1)
        return df


@click.command()
@click.option("--buffer", default=5000.0, help="Buffer zone for cobalt deposit")
def cobalt_heatmap(buffer: float):
    print(">>> Starting... >>>")
    start_time = time.time()
    BHM = BedrockHeatMap(buffer)
    BHM.cobalt.plot(column="probability", categorical=True, figsize=(20,20), cmap="RdYlGn")
    plt.savefig("cobalt.jpg")
    print(">>> Complete! >>>>")
    print("--- time elapse: %s seconds ---" % round((time.time() - start_time), 2))


if __name__ == "__main__":
    cobalt_heatmap()