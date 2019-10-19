This is a webapp that displays data about average delays at each station across the Melbourne Metropolitan Train Network, sourcing data from the Public Transport Victoria (PTV) public API (version 3).

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
1. Create a Google Cloud Project.
2. Navigate to 'Storage' in the google cloud console.
3. Navigate to 'Transfer' in the sidebar in the left-hand side of the page.
4. Copy from the Google Storage 'bucket' named 'ptv-services-data-dump' (select it as the source).
5. Follow the prompts to transfer an existing storage bucket into a new one. When creating a new bucket to transfer (i.e. copy into) as the 'destination' ensure that the bucket has 'Region' location type and choose 'australia-southeast1 (Sydney)' as the location. This bucket will be referred to as <your_bucket_name>.
6. Do not change any other settings and 'create'.

You now have access to a dump of the data from the original project/webapp, including station and route data. You can download this to your computer using google cloud tools as you see fit.

7. Run the following commands in a unix-like commandline/shell.

```bash
gcloud auth login
gcloud config set project <your-project-id>
gcloud datastore import gs://<your_bucket_name>/2019-10-19T13:54:02_88616/2019-10-19T13:54:02_88616.overall_export_metadata
cd default && gcloud app deploy
cd ..
cd background && gcloud app deploy background.yaml
```

8. Navigate to cloud scheduler and create a new job with the following settings:
- Frequency: * * * * *
- Target: App Engine HTTP
- URL: /monitor_services

The project should now be running on google cloud.
