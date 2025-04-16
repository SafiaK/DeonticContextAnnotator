#Take the url of act that needs annotation
#Download the act
#Convert the style according to the tool 

import requests
from style_Conversion import CleanDownloadedAct
from LegislationHandler import LegislationParser
import util
import shutil
import os
def download_legislation_act_as_xhtml(url,act_id,folder="downloaded_acts"):
    # Perform the GET request.
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad status codes

    act_id_output = act_id.replace("/","_")
    # Create the folder if it doesn't exist
    
    os.makedirs(folder, exist_ok=True)
    output_file = f"{folder}/{act_id_output}.xhtml"
    # Save the content to the output file as a .xhtml file.
    with open(output_file, 'wb') as f:
        f.write(response.content)
    
    print(f"Saved legislation act to: {output_file}")

if __name__ == "__main__":

    select_the_annotator_type = "old"
    act_id= '2010/15'
    act_id_output = act_id.replace("/","_")
    url_act = f"https://www.legislation.gov.uk/ukpga/{act_id}"
    url = f"{url_act}/data.xht?view=snippet&wrap=true"
    
    print("Downloading from:", url,act_id)
    download_legislation_act_as_xhtml(url,act_id)
    CleanDownloadedAct.process_folder("downloaded_acts", "processed_acts")

    if select_the_annotator_type == "new":
        parser_act = LegislationParser(url_act, False)
        print("Act Title:", parser_act.get_legislation_title())
        parser_act.get_title_tree(f"{act_id_output}_section_tree.json")
        util.update_script_js(f"{act_id_output}_section_tree.json")
        util.update_iframe_src(f"processed_acts/{act_id_output}.xhtml","index_with_selection.html")
    else:
        util.update_iframe_src(f"processed_acts/{act_id_output}.xhtml","index.html")



    # Create deployment package


    # Create package directory
    os.makedirs('package', exist_ok=True)

    # Copy required files and folders
    if select_the_annotator_type == "new":
        shutil.copy('index_with_selection.html', 'package/index.html')
    else:
        shutil.copy('index.html', 'package/index.html')
    shutil.copytree('styles', 'package/styles', dirs_exist_ok=True)
    shutil.copytree('scripts', 'package/scripts', dirs_exist_ok=True)
    shutil.copytree('processed_acts', 'package/processed_acts', dirs_exist_ok=True)

    # Create zip archive of package folder
    shutil.make_archive('package', 'zip', 'package')

    print("Pipeline completed successfully!")
    print(f"Package has been zipped to: package.zip")

