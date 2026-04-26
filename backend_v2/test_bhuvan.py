import httpx, asyncio
async def test():
    r=await httpx.AsyncClient().get('https://bhuvan-vec1.nrsc.gov.in/bhuvan/wms', params={'SERVICE':'WMS','VERSION':'1.1.1','REQUEST':'GetFeatureInfo','LAYERS':'lulc:BR_LULC50K_1112','QUERY_LAYERS':'lulc:BR_LULC50K_1112','BBOX':'73.6958,18.7643,73.6978,18.7663','WIDTH':'101','HEIGHT':'101','X':'50','Y':'50','INFO_FORMAT':'text/xml','SRS':'EPSG:4326'})
    print(r.text)
asyncio.run(test())
