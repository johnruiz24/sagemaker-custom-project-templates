apt-get update && apt-get install -y gcc git && apt-get -y install sudo  && apt-get clean
sudo apt-get install -y curl
curl --silent --location https://deb.nodesource.com/setup_16.x |sudo bash -
sudo apt-get install -y nodejs
sudo npm install -g aws-cdk@2.41.0