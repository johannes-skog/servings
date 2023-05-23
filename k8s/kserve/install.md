# Knative
```sh
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.10.1/serving-crds.yaml
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.10.1/serving-core.yaml
```

# kourier  
```sh
kubectl apply -f https://github.com/knative/net-kourier/releases/download/knative-v1.10.0/kourier.yaml
kubectl patch configmap/config-network \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'
```
# Install Cert Manager
```sh
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.11.0/cert-manager.yaml
```

# Install KServe built-in servingruntimes
```sh
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.10.1/kserve.yaml

kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.10.1/kserve-runtimes.yaml
```

# Increase the timout, needed for large images
```sh
kubectl patch cm config-deployment --patch '{"data":{"progressDeadline": "1200s"}}' -n knative-serving
```

# Domain mapping configuration 

It's is necessary because Knative Serving uses the HTTP Host header value to route requests to the correct service.

Add 
default.example.com: |
under data
kubectl edit configmap config-domain -n knative-serving

Use to patch the config:

```sh
kubectl patch configmap config-domain -n knative-serving --patch '{"data":{"default.example.com": ""}}'
```

# Disable isito ingress 
```sh
kubectl edit configmap/inferenceservice-config --namespace kserve
Add the flag `"disableIstioVirtualHost": true` under the ingress section
ingress : |- {
    "disableIstioVirtualHost": true
}
kubectl rollout restart deployment kserve-controller-manager -n kserve
```