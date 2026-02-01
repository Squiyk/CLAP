import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from matplotlib.offsetbox import OffsetImage, AnnotationBbox 


data = {
    'Syndrome': ['Stroke', 'Sturge-Weber Syndrome', 'Rasmussen\'s encephalitis', 'Cortical Dysplasia', 'Hemimegalencephaly'],
    'Gender': ['M', 'F', 'F', 'M', 'M'],  
    'Age_Diagnosis': [1, 0.5, 1, 0.5, 0.5],         
    'Age_Surgery': [6, 3, 6, 3, 1],         
    'Prognosis_Free_Pct': [80, 73, 63, 63, 50], 
    'Interictal_Contra_Pct': [13.5, 18.5, 18.9, 19.8, 23.5], 
    'Ictal_Contra_Pct': [22, 48.8, 32.8, 38.7, 45.3],        
    'Semiology': ['I, II/+', 'I, II/+', 'I', 'I', 'II/+'],
    'Features': ['', '', 'Epilepsia Partialis Continua', 'Infantile Spasms Less Likely', 'Infantile Spasms']
}

df = pd.DataFrame(data)

def get_scalpel_icon(path, zoom_level=0.035):
    try:
        arr_img = plt.imread(path)
        return OffsetImage(arr_img, zoom=zoom_level)
    except FileNotFoundError:
        print(f"Could not find image at {path}")
        return None

ICON_PATH = '/Users/xavier/Downloads/Scalpel Icon.png'

fig, (ax1, ax2, ax3) = plt.subplots(
    nrows=1, ncols=3, 
    figsize=(22, 7), 
    sharey=True, 
    gridspec_kw={'width_ratios': [3.5, 2, 2.8]} 
)

y_pos = np.arange(len(df))
syndrome_labels = df['Syndrome']

COLOR_BAR_LEFT = '#4c72b0'
COLOR_BAR_RIGHT = '#c44e52'
LINE_COLOR = '#7f7f7f'
TEXT_COLOR = '#333333'

ax1.hlines(y=y_pos, xmin=df['Age_Diagnosis'], xmax=df['Age_Surgery'], 
           color=LINE_COLOR, alpha=0.6, linewidth=2, zorder=1)

for i in range(len(df)):
    row = df.iloc[i]
    
    gender_symbol = "♂" if row['Gender'] == 'M' else "♀"
    color = '#1f77b4' if row['Gender'] == 'M' else '#e377c2'
    if row['Gender'] not in ['M', 'F']: 
        gender_symbol = "♂♀"
        color = '#555555'
        
    ax1.text(row['Age_Diagnosis'], i, gender_symbol, 
             va='center', ha='center', fontsize=18, fontweight='bold', 
             color=color, zorder=3, 
             bbox=dict(boxstyle="circle,pad=0.1", fc="white", ec="none", alpha=0.8))

    imagebox = get_scalpel_icon(ICON_PATH, zoom_level=0.025)
    
    
    ab = AnnotationBbox(imagebox, (row['Age_Surgery'], i), frameon=False)
    ax1.add_artist(ab)

    

    label = f"{row['Prognosis_Free_Pct']}% Free"
    ax1.text(row['Age_Surgery'] + 0.4, i, label, 
             va='center', ha='left', fontsize=10, fontweight='bold', color='green')

ax1.set_yticks(y_pos)
ax1.set_yticklabels(syndrome_labels, fontsize=12, fontweight='bold')
ax1.set_xlabel('Age (Years)', fontsize=10)
ax1.grid(axis='x', linestyle=':', alpha=0.4)

ax1.set_xlim(0, max(df['Age_Surgery']) + 3.0) 

ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

ax2.barh(y_pos, -df['Interictal_Contra_Pct'], color=COLOR_BAR_LEFT, align='center', height=0.5)
ax2.barh(y_pos, df['Ictal_Contra_Pct'], color=COLOR_BAR_RIGHT, align='center', height=0.5)

ax2.axvline(0, color='black', linewidth=0.8, alpha=0.5)
ax2.set_xlabel('Percentage (%)', fontsize=10)

ticks = ax2.get_xticks()
ax2.set_xticklabels([f'{int(abs(x))}' for x in ticks])
ax2.set_xlim(-60, 60) 
ax2.grid(axis='x', linestyle=':', alpha=0.4)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.spines['left'].set_visible(False)
ax2.tick_params(left=False) 

patch1 = mpatches.Patch(color=COLOR_BAR_LEFT, label='Interictal')
patch2 = mpatches.Patch(color=COLOR_BAR_RIGHT, label='Ictal')
ax2.legend(handles=[patch1, patch2], loc='upper left', bbox_to_anchor=(0, 1), frameon=False, fontsize=9)


ax3.axis('off')
ax3.set_ylim(ax1.get_ylim())

for i in range(len(df)):
    sem = df.loc[i, 'Semiology']
    feat = df.loc[i, 'Features']
    
    ax3.text(0.15, i, sem, va='center', ha='center', 
             fontsize=10, fontweight='bold', color=TEXT_COLOR)
    
    if feat:
        ax3.text(0.40, i, feat, va='center', ha='left', 
                 fontsize=9, color='#555555', linespacing=1.4)
    
    for ax in [ax1, ax2, ax3]:
        ax.axhline(i, color='grey', alpha=0.1, linewidth=1, zorder=0)


HEADER_Y = 1.03
HEADER_SIZE = 12
HEADER_WEIGHT = 'bold'

ax1.text(0.5, HEADER_Y, "Natural History & Prognosis", transform=ax1.transAxes,
         ha='center', va='bottom', fontsize=HEADER_SIZE, fontweight=HEADER_WEIGHT)

ax2.text(0.5, HEADER_Y, "Contralateral EEG Spikes", transform=ax2.transAxes,
         ha='center', va='bottom', fontsize=HEADER_SIZE, fontweight=HEADER_WEIGHT)

ax3.text(0.15, HEADER_Y, "Semiology", transform=ax3.transAxes,
         ha='center', va='bottom', fontsize=HEADER_SIZE, fontweight=HEADER_WEIGHT)

ax3.text(0.40, HEADER_Y, "Unique Features", transform=ax3.transAxes,
         ha='left', va='bottom', fontsize=HEADER_SIZE, fontweight=HEADER_WEIGHT)

ax1.invert_yaxis()
plt.subplots_adjust(left=0.20, right=0.95, wspace=0.1, top=0.85) 

plt.show()