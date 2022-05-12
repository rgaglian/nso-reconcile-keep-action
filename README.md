# NSO Reconcile Keep Action

Tested with NSO 5.8

This is a package that I created to show how we can create actions that limit NSO default service actions and expose them to some users.

In this case, we want to expose "service re-deploy reconcile" but not given the option for "discard-non-service-config"

I am showing three different ways to achieve the same objective. I am only committing one package that could be used for other service packages.

## Solution 1: Deviation.

In YANG, you can deviate action inputs. What you need to do is to add in your service YANG file or in a different module that you can call service-deviations.yang a deviation statement.

I am using the simple-mpls-vpn example that you can find in your NSO distribution by accesing:
$NCS_DIR/examples.ncs/service-provider/simple-mpls-vpn

What you need to do is:
1) Make your environment: %make all start
2) Edit the yang package: packages/l3vpn/src/l3vpn.yang
3) Add the following statement before the last curved bracket:

```
  deviation /l3vpn:vpn/l3vpn:l3vpn/l3vpn:re-deploy/l3vpn:input/l3vpn:reconcile/l3vpn:c-non-service-config/l3vpn:discard-non-service-config {
    deviate not-supported;
  }
```

4) Compile and load the package
5) Create a service: %set vpn l3vpn ....
6) Verify that the re-deploy action does not offer the option discard-non-service-config:

```
    admin@ncs% request vpn l3vpn test_tel re-deploy reconcile {
Possible completions:
  keep-non-service-config  }
```

Important Note: This option does not require NACM but also removes the "discard-non-service-config" to all users, including admin.

## Solution 2: Creating a "limited" re-deploy custom action

In this case, we will "copy" the service re-deploy action inside a separate module but we will remove one of the input options. Note that all other re-deploy options will be available for the user.

This was implemented in the action reconcile-keep-full and the python class ReconcileFullAction.

## Solution 3: Creating a "hand-crafted" re-deploy custom action

In this case, we do not use the input parameters from the default re-deploy aciton but we manually created what we believe are needed for our operators, you can follow a different logic that the original NSO design and even a different output format. In my case, I followed the same output schema.

In both Solutions 2 and 3, we will use NACM rules to set the previledges that some users have the right the use it.

## Testing:

Here is how it works:

1- clone this repository to a working environment, for example the "simple-mpls-vpn" example.
2- compile the package: % make -C packages/reconcile-keep/src clean all
3- perform package re-deploy
4- Add NACM rule to deny re-deploy and permit the new actions to the user oper:
```
set nacm rule-list oper group [ oper ]
set nacm rule-list oper rule rule_reconcile path /l3vpn:vpn/l3vpn:l3vpn/reconcile-keep action permit
set nacm rule-list oper rule rule_redeploy path /l3vpn:vpn/l3vpn:l3vpn/re-deploy action deny
set nacm rule-list oper rule rule_reconcile_full path /l3vpn:vpn/l3vpn:l3vpn/reconcile-keep-full action permit
```
5- login as "oper"
  Note: You need to do it via SSH or WebUI
6- try to execute the commands:
```
oper@ncs> request vpn l3vpn test_tel
Possible completions:
  check-sync          - Check if device config is according to the service
  commit-queue        -
  deep-check-sync     - Check if device config is according to the service
  get-modifications   - Get the data this service created
  log                 -
  reactive-re-deploy  - Reactive re-deploy of service logic
  reconcile-keep      -
  reconcile-keep-full -
  un-deploy           - Undo the effects of the service
oper@ncs>
```
---> You can see that re-deploy is missing now but the new "reconcile-keep" and "reconcile-keep-full" are available.

So, there are two options:
  reconcile-keep      - In this case the number of options were limited
  reconcile-keep-full - This is basically a copy of re-deploy but without the "bad input"

7- Test reconcile-keep which offers you only the inputs you hand-written:

```
admin@ncs% request vpn l3vpn test_tel reconcile-keep ?
Possible completions:
  dry-run  no-networking
```

8- Test reconcile-keep-full where all re-deploy options are available but the one you removed:
```
admin@ncs% request vpn l3vpn test_tel reconcile-keep-full reconcile {
Possible completions:
  keep-non-service-config  }
```

## Adding the new actions to all your services

You can add the new action to all your services, what you need to do is (using simple-mpls-vpn as example):

1) In the service YANG module (l3vpn.yang) add:
  - an import statement for the action module:
```
    import reconcile-keep {
      prefix reconcile-keep;
    }
```
  - add the grouping:
```
  container vpn {

    list l3vpn {
      description "Layer3 VPN";

      key name;
      leaf name {
        tailf:info "Unique service id";
        tailf:cli-allow-range;
        type string;
      }

      uses ncs:service-data;
      ncs:servicepoint  "l3vpn-template";

      // Add new action for reconcile
      uses reconcile-keep:grouping-reconcile-keep;
```

2) In your Makefile, add the yangpath to the action package:
```
YANGPATH = --yangpath ./yang --yangpath ../../reconcile-keep/src/yang
```

3) In your package-meta-data.xml add the dependency:

```
<ncs-package xmlns="http://tail-f.com/ns/ncs-packages">
  <name>l3vpn</name>
  <package-version>1.0</package-version>
  <description>Skeleton for a resource facing service - RFS</description>
  <ncs-min-version>3.0</ncs-min-version>
  <required-package>
      <name>reconcile-keep</name>
  </required-package>
</ncs-package>
```

4) Make the package and apply "package re-deploy"

Note: the action can also be added using the augment statement.