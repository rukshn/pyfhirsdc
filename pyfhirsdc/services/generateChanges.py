import logging
import pandas as pd 
from pathlib import Path

from pyfhirsdc.config import get_dict_df
from pyfhirsdc.serializers.utils import get_page_content_path, write_page_content

logger = logging.getLogger("default")

# This function reads the DAK-Intermediate file and returns the changes
def parseChanges():
    changes = []
    df_changes = get_dict_df()['changes']
    if (len(df_changes.index) > 0):
        return df_changes
    else:
        return None         

# Write the changelog to the changes.md file in the IG
# By using the changes collected from the parseChanges() file
def generateChagnes():
    
    logger.info("processing changes................")
    dfs_changes = parseChanges()

    if dfs_changes is not None:
        fileContent = []
        for index, row in dfs_changes.iterrows():
            logger.info("Saving changes for %s", row[1])
            fileContent.append(f"""
## {row['date']} - {row['version']}

{row['change']}
                               """)
        
        changes_file_path = get_page_content_path("/", "changes.md")
        write_page_content(changes_file_path, "Changes", "\n".join(fileContent))