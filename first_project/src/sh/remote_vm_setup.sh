# Set up gcloud vm
gcloud compute instances create tophers-vm-1 --project=fluted-citizen-269819 --zone=us-central1-a --machine-type=e2-medium --network-interface=network-tier=PREMIUM,subnet=default --provisioning-model=STANDARD --service-account=614936797883-compute@developer.gserviceaccount.com --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append --create-disk=auto-delete=yes,boot=yes,device-name=tophers-vm-1,image=projects/debian-cloud/global/images/debian-11-bullseye-v20220822,mode=rw,size=10,type=projects/fluted-citizen-269819/zones/us-central1-a/diskTypes/pd-balanced --no-shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring --reservation-affinity=any

# Set up local ssh for connecting to machine
gcloud compute config-ssh

# get external IP
gcloud compute instances describe --project=fluted-citizen-269819 --zone=us-central1-a  tophers-vm-1 --format='get(networkInterfaces[0].accessConfigs[0].natIP)'

# ssh directly
gcloud compute ssh --project=fluted-citizen-269819 --zone=us-central1-a tophers-vm-1 

# stop instance
gcloud compute instances stop --project=fluted-citizen-269819 --zone=us-central1-a tophers-vm-1

# delete instance
gcloud compute instances delete tophers-vm-1 --zone=us-central1-c