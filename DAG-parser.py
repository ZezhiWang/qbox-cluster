import json
import sys
import yaml
import os
import shutil
import stat

class TerraformTemplate:
    def __init__(self, tfvars, services):
        self.tfvars = tfvars
        string = ""
        for i, s in enumerate(services):
            if i != 0:
                string += " && "
            string += f"kubectl create configmap {s}-configmap --from-file test/{s}/config.yaml"
        f = open(tfvars, "r")
        v_str = f.read()
        self.template = v_str + f"""
bookinfo_apps_path = "test/test.yaml"
add_configmap = "{string}"
"""
        f.close()
    def write2file(self, f):
        f.write(self.template)

class DeploymentTemplate:
    def __init__(self, name, bad, middle):
        self.template = \
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": name,
                    "labels": {
                        "app": name,
                        "version": "v1"
                    }
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": {
                            "app": name,
                            "version": "v1"
                        }
                    },
                    "template": {
                        "metadata": {
                            "labels": {
                                "app": name,
                                "version": "v1"
                            }
                        },
                        "spec": {
                            "containers": [
                                {
                                    "name": name,
                                    "image": "docker.io/cs2952fspring2020amahajcwu/fake-service:latest" if not bad \
                                        else "docker.io/cs2952fspring2020amahajcwu/fake-service-bad:latest",
                                    "imagePullPolicy": "Always",
                                    "ports": [
                                        {
                                            "containerPort": 9080
                                        }
                                    ],
                                    "env": [{
                                        "name": "NAME",
                                        "value": name
                                    }],
                                }
                            ]
                        }
                    }
                }
            }
        if middle:
            self.template["spec"]["template"]["spec"]["containers"][0]["env"].append({
                "name": "MIDDLE",
                "value": "True"
            })
            self.template["spec"]["template"]["spec"]["containers"].append(
                {
                    "name": "qbox",
                    "image": "docker.io/cs2952fspring2020amahajcwu/qbox:latest",
                    "imagePullPolicy": "Always",
                    "ports": [
                        {
                            "containerPort": 3001
                        }
                    ],
                    "volumeMounts": [
                        {
                            "name": "config-volume",
                            "mountPath": "/configuration/"
                        }
                    ]
                }
            )
            self.template["spec"]["template"]["spec"]["volumes"] = [
                    {
                        "name": "config-volume",
                        "configMap": {
                            "name": f"{name}-configmap"
                        }
                    }
                ]
    def get_file(self):
        return self.template

class ServiceTemplate:
    def __init__(self, name):
        self.template =  \
        {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": name,
                "labels": {
                    "app": name,
                    "service": name
                }
            },
            "spec": {
                "ports": [
                    {
                        "port": 9080,
                        "name": "http"
                    }
                ],
                "selector": {
                    "app": name
                },
                "type": "LoadBalancer"
            }
        }
    
    def get_file(self):
        return self.template

class FileTemplate:
    def __init__(self):
        self.template = \
            {
                "host": None,
                "matchRequest": {
                    "headers": {
                        "Start-Faking": "True"
                    },
                    "method": "GET",
                    "url": "http://localhost:3001/"
                },
                "onAllSucceeded": {
                    "body": None,
                    "status-code": 200
                },
                "onAnyFailed": {
                    "body": None,
                    "status-code": 500
                },
                "onMatchedRequest": []
            }

    def construct_add(self, service, obj):
        down_stream = obj["edges"][service]
        self.template["host"] = service + ".svc"
        body = ""
        for i, s in enumerate(down_stream):
            body += f"{s}: ${{transaction[{i}].response.body}}\n"
        self.template["onAllSucceeded"]["body"] = body
        self.template["onAnyFailed"]["body"] = body
        self.template["matchRequest"]["url"] += "add/"
        for s in down_stream:
            request_template = onMatchedRequest_template()
            if s in obj["edges"].keys():
                request_template[
                    "url"] = f"http://{s}.default.svc:9080/saga-add/${{parent.headers.Product-Id}}"
                request_template["onFailure"][0][
                    "url"] = f"http://{s}.default.svc:9080/saga-delete/${{root.headers.Product-Id}}"

            else:
                request_template[
                    "url"] = f"http://{s}.default.svc:9080/add/${{parent.headers.Product-Id}}"
                request_template["onFailure"][0][
                    "url"] = f"http://{s}.default.svc:9080/delete/${{root.headers.Product-Id}}"
            self.template["onMatchedRequest"].append(request_template.template)

    def construct_delete(self, service, obj):
        down_stream = obj["edges"][service]
        self.template["host"] = service + ".svc"
        body = ""
        for i, s in enumerate(down_stream):
            body += f"{s}: ${{transaction[{i}].response.body}}\n"
        self.template["onAllSucceeded"]["body"] = body
        self.template["onAnyFailed"]["body"] = body
        self.template["matchRequest"]["url"] += "delete/"
        for s in down_stream:
            request_template = onMatchedRequest_template()
            if s in obj["edges"].keys():
                request_template[
                    "url"] = f"http://{s}.default.svc:9080/saga-delete/${{parent.headers.Product-Id}}"
                request_template["onFailure"][0][
                    "url"] = f"http://{s}.default.svc:9080/saga-add/${{root.headers.Product-Id}}"

            else:
                request_template[
                    "url"] = f"http://{s}.default.svc:9080/delete/${{parent.headers.Product-Id}}"
                request_template["onFailure"][0][
                    "url"] = f"http://{s}.default.svc:9080/add/${{root.headers.Product-Id}}"
            self.template["onMatchedRequest"].append(request_template.template)


class onMatchedRequest_template:
    def __init__(self):
        self.template = \
            {
                "isSuccessIfReceives": [
                    {
                        "headers": {
                            "Content-type": "application/json"
                        },
                        "status-code": 200
                    }
                ],
                "maxRetriesOnTimeout": 3,
                "method": "GET",
                "onFailure": [
                    {
                        "isSuccessIfReceives": [
                            {
                                "headers": {
                                    "Content-type": "application/json"
                                },
                                "status-code": 200
                            }
                        ],
                        "maxRetriesOnTimeout": 1,
                        "method": "GET",
                        "timeout": 3,
                        "url": None
                    }
                ],
                "timeout": 30,
                "url": None
            }

    def __getitem__(self, key):
        return self.template[key]

    def __setitem__(self, key, value):
        self.template[key] = value

class ScriptTemplate:
    def __init__(self, services, first_service):
        add_configmap = ""
        for s in services:
            add_configmap += f"kubectl create configmap {s}-configmap --from-file {s}/config.yaml\n"

        self.run_template = f"""#!/bin/bash
{add_configmap}
kubectl apply -f test.yaml

sleep 10
kubectl get svc
echo
serviceip=$(kubectl get svc | grep {first_service} | cut -d ' ' -f 9)
kubectl get pods
podname=$(kubectl get pods | grep {first_service} | cut -d ' ' -f 1)
curl ${{serviceip}}:9080/saga-add/1
sleep 1
echo
kubectl logs ${{podname}} qbox
echo
echo
kubectl logs ${{podname}} {first_service}
"""
        delete_configmap = ""
        for s in services:
            delete_configmap += f"kubectl delete configmap {s}-configmap\n"
        self.stop_template = f"""#!/bin/bash
{delete_configmap}
kubectl delete -f test.yaml        
"""
    def get_stop_script(self):
        return self.stop_template

    def get_run_script(self):
        return self.run_template


def config_generator(file, tfvars, dir='.'):
    if os.path.isdir(os.path.join(dir, "test")):
        # print("here")
        shutil.rmtree(os.path.join(dir, "test"))
    os.mkdir(os.path.join(dir, "test"))
    # shutil.copytree(os.path.join(dir, "lib"), os.path.join(dir, "test"))

    f = open(file, "r")
    obj = json.load(f)
    f.close()
    root = obj["root"]

    test_yaml = []
    services = []

    for service in obj["nodes"]:
        if service in obj["edges"]:
            services.append(service)
            os.mkdir(os.path.join(dir, "test", service))
            f = open(os.path.join(dir, "test", service, "config.yaml"), "w")
            file_template = FileTemplate()

            file_template.construct_add(service, obj)
            if root != service:
                file_template_delete = FileTemplate()
                file_template_delete.construct_delete(service, obj)
                yaml.safe_dump_all(
                    [file_template.template, file_template_delete.template], f)
            else:
                yaml.safe_dump(file_template.template, f)
            f.close()
        test_yaml.append(DeploymentTemplate(service, service in obj["bad"], service in obj["edges"]).get_file())
    
    for service in obj["nodes"]:
        test_yaml.append(ServiceTemplate(service).get_file())
    f = open(os.path.join(dir, "test", "test.yaml"), "w")
    yaml.safe_dump_all(test_yaml, f)
    f.close()
    f = open(os.path.join(dir, "test", "run.sh"), "w")
    t = ScriptTemplate(services, obj["root"])
    f.write(t.get_run_script())
    f.close()
    f = open(os.path.join(dir, "test", "stop.sh"), "w")
    f.write(t.get_stop_script())
    f.close()
    st = os.stat(os.path.join(dir, "test", "run.sh"))
    os.chmod(os.path.join(dir, "test", "run.sh"), st.st_mode | stat.S_IEXEC)
    st = os.stat(os.path.join(dir, "test", "stop.sh"))
    os.chmod(os.path.join(dir, "test", "stop.sh"), st.st_mode | stat.S_IEXEC)

    f = open(os.path.join(dir, "test", "values.tfvars"), "w")
    t = TerraformTemplate(tfvars, services)
    t.write2file(f)
    f.close()


if __name__ == "__main__":
    config_generator(sys.argv[1], sys.argv[2])
