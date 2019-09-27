##Initialisation
Under Construction.

##Webapp
<i>In order to run the web app locally via the webserver:</i>
```bash
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
cd webapp
python main.py
```
##Monitoring Service
In order to run the python script that harvests train punctuality data and populates the google cloud database, run the following in a bash shell from the root directory:
```bash
cd background && python api_tools.py
```

##Deployment to Google Cloud
###Google App Engine
Under construction.