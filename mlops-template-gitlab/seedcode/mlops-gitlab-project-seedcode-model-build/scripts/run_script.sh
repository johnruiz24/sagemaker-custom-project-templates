root=$1
folder=$2
file_name=$3
execute_flag=$4

pip install --upgrade pip
pip install -r "${root}"/requirements.txt
aws configure set region $TF_VAR_aws_region
python3 "${root}"/"${folder}"/"${file_name}" "${execute_flag}"