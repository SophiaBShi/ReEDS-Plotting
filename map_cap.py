#!/usr/bin/env python
# coding: utf-8


# In[2]:


import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import os, sys, math, site
import geopandas as gpd
print('done')


# ## Modify me

# In[2]: 

# Data Organization

# output path
folder = os.path.expanduser('Z:\\FY24-sshi-Last10pctProject\\national runs\\decarb plots')
outpath = os.path.join(folder, 'maps') 
reedspath = 'C:\\Users\sshi\\Documents\\GitHub\ReEDS-2.0'

# run(s) we are interested in studying
scenarios = ['Z:\\FY24-sshi-Last10pctProject\\national runs\\1_USA_noFC_BAU']


#BAs to include for each region 
wecc_bas = [f'p{x}' for x in range(1,35)]
wecc_bas.append('p59')
ercot_bas =  ['p60', 'p61', 'p62','p63','p64','p65','p67']
national_bas = [f'p{x}' for x in range(1,135)]

#change value of conus_bas to select desired region for plot
conus_bas = national_bas


hierarchy = pd.read_csv(
    os.path.join(reedspath,'inputs','hierarchy.csv')
)#.rename(columns={'*r':'r'}).set_index('r')

#filter out canada/mexico
hierarchy = hierarchy.loc[hierarchy.country=='USA'].copy()

# list BA in each transmission planning region 
transreg2r = pd.Series(
    index=hierarchy.transreg.values,
    data=hierarchy.index
).groupby(level=0).agg(list)

#extract BA and state columns
r2st = pd.Series(
    
    index= hierarchy.index,
    data=hierarchy.st.values   
) #.groupby(level=0).agg(list)


# Select year to filter data for 
year = 2050


# List of techs in outputs
tech_list = pd.read_csv(os.path.join(scenarios[0],'outputs','cap.csv')).iloc[:,0]

#List of techs you want to plot
tech_name = ['H2-CT' ]

# select spatial resolution of run 
agg_level = 'r' # choose 'st' for the state level or 'r' for the ReEDS BA level, 'county' for county, mixed for mixed resolution runs
# select spatial resolution label for plot title 
agg_plot = 'BA' 


# Obtain capacity data by region and tech type 

for scenario in scenarios:
    
    if agg_level == 'county':
        df = pd.read_csv(os.path.join(scenarios,'outputs','cap.csv')).rename(columns = {'Dim1':'i','Dim2':'r', 'Dim3':'t', 'Value': 'capacity_MW'})
          
        hier_sub = hierarchy[['county','ba']]
        county2ba = hier_sub.set_index('county')['ba'].to_dict()
        df['ba'] = df['r'].map(county2ba)
        df = df.groupby(by=['ba','t','i'], as_index=False).sum() 
        df = df.drop(columns ='r')
        df = df.rename(columns={'ba':'r'})
    
    else:
        # pull in the capacity data from selected scenario
        df = pd.read_csv(os.path.join(scenario,'outputs','cap.csv')).rename(columns = {'Dim1':'i','Dim2':'r', 'Dim3':'t', 'Value': 'capacity_MW'})
        #df = df[df['i'].isin(tech_list)] # filter to only include desired techs
    
    df = df[df['i'].isin(tech_list)] # filter to only include desired techs
      
    #seperate each tech into seperate df      
    cap_by_tech = {}
    
    for idx in tech_name:
       
        if agg_level =='county':
            cap_by_tech[idx] = df[df['i'].str.contains(idx)] 
        
            #group the same year and in the same region for each data frame
            cap_by_tech[idx] = cap_by_tech[idx].groupby(by=['r','t'], as_index=False).sum() 
            
            #take capaicty for last modeled year in each region 
            cap_by_tech[idx] = cap_by_tech[idx][cap_by_tech[idx]['t'] == year]
            cap_by_tech[idx]['capacity_GW'] = cap_by_tech[idx]['capacity_MW']/10**3
            #cap_by_tech[idx] = cap_by_tech[idx].rename(columns = {'ba' : 'r'})

            
        else:
            cap_by_tech[idx] = df[df['i'].str.contains(idx)] 
            
           
            #group the same year and in the same region for each data frame
            cap_by_tech[idx].groupby(by=['r','t'], as_index=False).sum() 
            
            #take capaicty for last modeled year in each region 
            cap_by_tech[idx] = cap_by_tech[idx][cap_by_tech[idx]['t'] == year]
            cap_by_tech[idx]['capacity_GW'] = cap_by_tech[idx]['capacity_MW']/10**3
    
    
        if agg_level == 'st':
            
            # map the r column to states and aggregate up
            #already at state level since scenario was run at state level, not BA
    # =============================================================================
    #         df['st'] = df['r'].map(r2st)
    #         df = df.groupby(by=['st'], as_index=False).sum() # group by year to aggregate all techs
    # =============================================================================
            cap_by_tech[idx] = cap_by_tech[idx].rename(columns={'r':'st'})
    
            # get the states with 0s to show up on the map
            conus_states = ['AL','AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
            state_df = pd.DataFrame(conus_states,columns={'st'})
            cap_by_tech[idx] = state_df.merge(cap_by_tech[idx],how='left').fillna(0)
            
            # pull in the state region shapefile
            reeds_gdf = gpd.read_file(os.path.join(reedspath,r'inputs','shapefiles','WKT_csvs','st_WKT.csv'))
            
        elif agg_level == 'r':
            ba_df = pd.DataFrame(conus_bas,columns=['r'])
            cap_by_tech[idx] = ba_df.merge(cap_by_tech[idx],how='left').fillna(0)
            #df_cap_ba = ba_df.merge(cap_by_tech[idx],how='left').fillna(0)
            cap_by_tech[idx] = cap_by_tech[idx].groupby(by = ['r']).sum()
            # pull in the BA region shapefile
            reeds_gdf = gpd.read_file(os.path.join(reedspath,'inputs','shapefiles','US_PCA','US_PCA.shp')).rename(columns = {'rb':'r'})
        
        elif agg_level =='county' or agg_level =='mixed':
            ba_df = pd.DataFrame(conus_bas,columns=['r'])
            cap_by_tech[idx] = ba_df.merge(cap_by_tech[idx],how='left').fillna(0)
            #df_cap_ba = ba_df.merge(cap_by_tech[idx],how='left').fillna(0)
            cap_by_tech[idx] = cap_by_tech[idx].groupby(by = ['r']).sum().reset_index()
            # pull in the BA region shapefile
            reeds_gdf = gpd.read_file(os.path.join(reedspath,'inputs','shapefiles','US_PCA','US_PCA.shp')).rename(columns = {'rb':'r'})
        
        else:
            print('Invalid input for agg_level parameter.')
            pass
                                      
#%% 

# Plotting

# For county level runs set agg_level to r to get county summed to BA plots 
if agg_level =='county' or agg_level =='mixed':
    agg_level = 'r'

# plot 
plt.figure(figsize = (25,25))

for count, tech_names in enumerate (tech_name):

    n_rows = int(len(tech_name)/2)
    n_cols = int(len(tech_name)/2)
    #ax = plt.subplot(n_rows,n_cols,count +1 )  #sharex=True,sharey=True) #)
    ax = plt.subplot(1,3,count +1 )  #sharex=True,sharey=True) #)
    
   
    dfmap = reeds_gdf.merge(cap_by_tech[tech_name[count]], how='inner', on=agg_level)
    vmax = dfmap['capacity_GW'].max()

    # plot the data where the colors are based on the cap
    if count == 0:
        dfmap.plot(ax=ax, column='capacity_GW',cmap='Blues',legend=True,edgecolor="black", linewidth=0.3,legend_kwds={'shrink': 0.1, 'label' : 'Capacity GW'}, vmax = vmax, figsize=(7,6))
        
    else:
        dfmap.plot(ax=ax, column='capacity_GW',cmap='Blues',legend=True,edgecolor="black", linewidth=0.3,legend_kwds={'shrink': 0.1, 'label' : 'Capacity GW'}, vmax = vmax,figsize=(7,6))

    
    agg_name = agg_plot
        # other plotting configuration  
    ax.patch.set_facecolor('white') # set background of image to white
   
   # plot name formatting 
    # if tech_name[count] == 'pv' :
    #      tech_name[count] = tech_name[count].upper()
    # else:
    #     tech_name[count] = tech_name[count].capitalize()

    #ax.set_title(f'Fuel Cells: Decarb', fontsize = 12, fontweight="bold")

    dfmap['coords'] =  dfmap['geometry'].apply(lambda x:x.representative_point().coords[:])
    dfmap['coords'] = [coords[0] for coords in dfmap['coords']]
    
    # if tech_names =='pv':
    #     for idx, row in dfmap.iterrows():
    #         ax.annotate(xy =row['coords'], text = row['r'], horizontalalignment = 'center', color = 'red', size = 6)
    
    ax.axis('off')
    
  
    plt.tight_layout()

    outpath = 'Z:\\FY24-sshi-Last10pctProject\\national runs\\decarb plots'
    plt.savefig(os.path.join(outpath,f'{tech_name}_{year}_{agg_level}.svg'),dpi=350)
    plt.show()

       

     
     




# %%
