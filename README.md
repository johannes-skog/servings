# Kserve

KServe is a project developed by the Kubernetes community focused on serving machine learning models in a cloud-native fashion. KServe provides a Kubernetes Custom Resource Definition for serving machine learning models across various frameworks, automating the entire process of model serving. It offers dynamic autoscaling, rollout and rollback, as well as serverless capabilities.

One of the distinctive features of KServe is its support for Transformers. This simplifies the deployment of models that necessitate custom pre- and post-processing. With KServe's Transformer component, you can bypass the need to write a custom backend in C or C++ and generate a shared library file, which would be the case when using the Nvidia Triton Inference Server directly. Instead, you can write your pre- and post-processing logic in Python and deploy it as part of your serving infrastructure. This considerably decreases the complexity of deploying custom models.

The Transformer operates as an individual pod in your serving deployment, acting as an intermediary between the predictor (the model server) and the user requests. It's capable of transforming the input request before it's forwarded to the predictor, and it can also transform the prediction output before it's returned to the user.

This setup allows you to divide pre-processing, prediction, and post-processing into separate pods. The prediction pod can leverage optimized Docker containers, such as the Nvidia Triton Inference Service. This way, we can handle the serving of complex models more effectively, separating concerns and enhancing the maintainability and scalability of the system.


# For local testing 

Install Kubernetes on you local machine.

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

## Set up the load balancer for a bare-metal clusters

```sh
microk8s enable metallb
```

## Install kserve and all dependencies 

To install kserve, follow the guide in 
```
./k8s/kserve/install.md
```

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

# Deploy 

Create the Kubernetes secrets,

```sh
kubectl apply -f k8s/kserve/create-azure-secret.yaml
```

Set up a message dumper that will log all CloudEvents from the predictor and transformer

```sh
kubectl apply -f k8s/kserve/message-dumper.yaml
```

Deploy the inference service

```sh
kubectl apply -f k8s/kserve/deploy_w_transformer.yaml
```


To get information about the deployed inference service, e.g getting the host names for the predictor and transformers:
```sh
kubectl describe inferenceservice -n default <model_name>
```

To delete inferenceservices 

```sh
kubectl delete inferenceservice -n default <model_name> # not pod name
```

To get all deployed knative services, i.e. the inferenceservices.

```sh
kubectl get ksvc -A
```


# Inference on the Trition Inference Serve 

Remember to set the appropriate Host header (Host: test-predictor-default.default.example.com) in your HTTP requests to route them to the correct service.

```sh
curl -v -H "Host: test-predictor-default.default.example.com" -H "Content-Type: application/json" -X POST -d "@example_inputs/input-triton.json" "http://10.64.140.44:80/v2/models/test/infer" 
```

Where the ip address is LoadBalancer kourier external IP address.

The load balancers Ip address you can find by listing all deployed services:

```sh
kubectl get svc -A
```

## Test the API

We can send in a `request_id` in the header 

```sh
-H "x-request-id: 121341"
```

## With port forwarding 
```sh
kubectl port-forward test-transformer-default-00001-deployment-68df4b8bb8-lsqwq 8089:8080
```
```sh
curl -v -H "x-request-id: 121341" -H "Content-Type: application/json" -X POST -d "@example_inputs/input-triton.json" localhost:8089/v2/models/test/infer
```

## Routed by the load balancer
```sh
curl -v -H "x-request-id: 121341" -H "Host: test-transformer-default.default.default.example.com" -H "Content-Type: application/json" -X POST -d "@example_inputs/input-triton.json" "http://10.64.140.43:80/v2/models/test/infer"
```
or dicecly to the predictor, bypassing pre/post processing

```sh
curl -v -H "x-request-id: 121341" -H "Host: test-predictor-default.default.default.example.com" -H "Content-Type: application/json" -X POST -d "@example_inputs/input-triton.json" "http://10.64.140.43:80/v2/models/test/infer"
```

## Stress test the deployment

To conduct load testing of your API deployed on Kubernetes using Apache JMeter After installation, you create a new test plan in JMeter. Within this test plan, you add a Thread Group, which represents a set of users that JMeter will simulate to apply load on your application.

You then configure an HTTP Request under this Thread Group with the details of your server and the API endpoint you want to test. You also need to add the necessary HTTP headers, see above, and the JSON body, copy the content from example_inputs/input-triton.json,  for the POST request.

Next, you add a Listener to the Thread Group in JMeter. A Listener is a component that allows you to view the results of the load test in various formats.

Once your test plan is set up, you run the test in JMeter. As JMeter applies load on your application, you monitor the behavior of your Kubernetes deployment. 

```sh
watch -n 0.1 kubectl get pods
```

You want to check whether the number of pods scales up or down as the load increases or decreases, thus verifying if the autoscaling feature of your Kubernetes deployment is working as expected.



