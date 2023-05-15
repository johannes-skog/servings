## Nvidia Triton Inference Server

To deploy custom models using the Nvidia Triton Inference Server, you can utilize the default backends, with the exception that the request should be directly sent to the model. However, if you require custom pre/post processing outside of the model, you will need to develop a custom backend in C or C++ and create a shared library file. This additional step can add complexity to the deployment process for custom models.


# For local testing 

## Install microk8s

```sh
sudo snap install microk8s --classic --channel=1.26
```

Set the owner of the kube folder to be the current user. Export the microk8s config to config, to make it exposed to kubectl

```sh
sudo chown -f -R $USER ~/.kube
cd $HOME
mkdir .kube
cd .kube
microk8s config > config
```

## Set up GPU
```sh
microk8s enable gpu
sudo snap restart microk8s
```

It can take some time to setup the gpu-resource pods, keep a look at them at:

```sh
kubectl get pods -A
```

Test that the k8s  instance has gpu support 
```sh
microk8s kubectl logs -n gpu-operator-resources -lapp=nvidia-operator-validator -c nvidia-operator-validators
```

Deploy a test run to the cluster

```sh
microk8s kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: cuda-vector-add
spec:
  restartPolicy: OnFailure
  containers:
    - name: cuda-vector-add
      image: "k8s.gcr.io/cuda-vector-add:v0.1"
      resources:
        limits:
          nvidia.com/gpu: 1
EOF
```

look at the logs
```sh
microk8s kubectl logs cuda-vector-add
```

## Set up the cluster

Setup load balancer

```sh
microk8s enable metallb
```

Set up the ingress 

```sh
microk8s enable community
microk8s.enable istio
```

# Setup Kfserve

To setup Kfserve, we need to deploy knative, kourier, cert-manager to the cluster, follow these guides,


```
https://knative.dev/docs/install/yaml-install/serving/install-serving-with-yaml/#verifying-image-signatures
```
and
```
https://cert-manager.io/docs/installation/
```

Now, kserve can be deployed to the cluster

```sh
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.8.0/kserve.yaml

kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.8.0/kserve-runtimes.yaml
```

keep a look at the status of the pods to see that everything has been setup correcly,

```sh
 kubectl get pods -A
```

To deploy a inferenceservices running nvidia-triton infernce server to the cluster,

```sh
kubectl apply -f k8s/kserve/deploy.yaml
```


```sh
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: test
spec:
  predictor:
    minReplicas: 1
    timeout: 60
    batcher:
      maxBatchSize: 32
      maxLatency: 500
    serviceAccountName: sa
    triton:
      args:
      - --log-verbose=1
      storageUri: https://deeplearning.blob.core.windows.net/kfserve2/models/
      runtimeVersion: 20.10-py3
```


kserve will fetch the model and config files from the storageUri. We need to setup a kubernetes secrets that contains the connection details for the blob storage uri link. 

## Setting up Service Principle for Blob Storage Account 

```
az ad sp create-for-rbac --name kserve \
                         --role "Storage Blob Data Owner" \
                         --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/providers/Microsoft.Storage/storageAccounts/kserve
```

it will return 

```
{
  "appId": "",
  "displayName": "",
  "password": "",
  "tenant": ""
}
```

where appId is client_id, password, client_secret.

From that we can now set up kubernetes secrets containing the connection details. The ServiceAccount can later be used when we are deploying an InferenceService.

```
apiVersion: v1
kind: Secret
metadata:
  name: azcreds
type: Opaque
stringData: # use `stringData` for raw credential string or `data` for base64 encoded string
  AZ_CLIENT_ID: xxxx
  AZ_CLIENT_SECRET: xxxx
  AZ_SUBSCRIPTION_ID: xxxx
  AZ_TENANT_ID: xxxx
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sa
secrets:
- name: azcreds
```


To delete inferenceservices 

```sh
kubectl delete inferenceservice -n default <model_name> # not pod name
```

# Inference on the Trition Inference Serve 

Remember to set the appropriate Host header (Host: test-predictor-default.default.example.com) in your HTTP requests to route them to the correct service.

```sh
curl -v -H "Host: test-predictor-default.default.example.com" -X POST -d "@example_inputs/input-triton.json" "http://10.64.140.44:80/v2/models/test/infer" 
```

Where the ip address is LoadBalancer kourier external IP address 
