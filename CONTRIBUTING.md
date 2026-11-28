# How to contribute to qb-natpmp

This document tells you how to change this repository. The
[README](README.md) tells you what the helper does and how to configure it.

## Pull requests

- Make each change on a branch. Then open a pull request into `main`.
- If you do not have write access, fork the repository. Open the pull
  request from your fork.
- This repository is public. For a first-time contributor, GitHub Actions
  runs the workflows only after the owner approves them.
- The `Test` workflow runs on each pull request and on each push to `main`.
  Wait until it passes before you merge.
- `main` has no branch protection and no required checks. Thus, GitHub
  does not stop a merge before the `Test` workflow passes.
- Use a squash merge. GitHub uses the title of the pull request as the
  commit title on `main`. If the pull request has only one commit, GitHub
  uses the title of that commit.

## Commit messages

Use the Conventional Commits form for each commit title and for the title of
the pull request:

```text
<type>: <summary>
<type>(<scope>): <summary>
```

- Recent titles use `fix:`, `ci:` and `chore(deps):`.
- Start the summary with a lowercase verb in the base form, for example
  "accept", "make" or "rebuild".
- If the title does not give the reason for the change, add a body.
- Renovate writes its own titles with the `chore(deps):` prefix.

These titles come from the history of `main`. GitHub adds the number of the
pull request, for example `(#3)`, at the squash merge:

```text
fix: accept qBittorrent HTTP 204 authentication responses
ci: rebuild and publish the image automatically on Renovate updates (#3)
chore(deps): Update dependency python to 3.15 (#4)
```

## Run the checks locally

These commands do the same checks as the `Test` workflow. Run them before
you open a pull request:

```sh
python3 -m pip install --require-hashes -r requirements.lock
python3 -m unittest discover -s tests -v
docker build --tag qb-natpmp:test .
docker run --rm --entrypoint python3 qb-natpmp:test \
  -c 'import run, health, natpmp, qbittorrent; assert not health.check_health()'
```

- CI uses Python 3.15. The base image in the `Dockerfile` has the same
  Python version. The header of `requirements.lock` also names it. A test
  fails if these Python versions differ.
- The unit tests do not need a VPN or a live qBittorrent.
- The last command checks that the image can import all modules. It also
  checks that `health.check_health()` returns `False` when no health marker
  exists.

## Releases

When Renovate merges a change to a file that goes into the image,
`auto-release.yml` creates the next patch release. These files go into the
image:

- `Dockerfile`
- `requirements.lock`
- `entrypoint.sh`
- `run.py`, `natpmp.py`, `qbittorrent.py` and `health.py`

The owner releases all other changes by hand. A published GitHub release
starts `docker-publish.yml`. `auto-release.yml` calls `docker-publish.yml`
directly, because a release from `GITHUB_TOKEN` does not start
`docker-publish.yml`.

- Release tags use the form `vX.Y.Z`, for example `v1.1.2`.
  `auto-release.yml` adds 1 to the patch number of the latest release.
- `docker-publish.yml` builds the image for `linux/amd64` and `linux/arm64`.
- It pushes `ghcr.io/coderpunch/qb-natpmp` with the tags `vX.Y.Z`, `X.Y.Z`,
  `X.Y`, `X` and `latest`.

## Python dependencies

`requirements.txt` pins the direct dependencies. `requirements.lock` pins all
packages with their hashes. The image and CI install only
`requirements.lock`, with `--require-hashes`. The image uses the `pip` of the
Python base image.

To change a dependency by hand, do these steps:

1. Change the pin in `requirements.txt`.
2. Regenerate `requirements.lock` with pip-tools. Use the Python version that
   the header of `requirements.lock` names:
   ```sh
   pip-compile --allow-unsafe --generate-hashes --no-emit-index-url \
     --output-file=requirements.lock --strip-extras requirements.txt
   ```
3. Run the checks in [Run the checks locally](#run-the-checks-locally).

## Secrets

- Do not commit a secret to this repository. This repository is public.
- Give the qBittorrent credentials to the helper only at runtime, through
  `QB_USER` and `QB_PASS`.
- Use placeholder values in tests and examples.

The workflows use only the `GITHUB_TOKEN` of GitHub Actions. They need no
repository secret.

## Renovate

`renovate.json` configures Renovate. Renovate keeps these versions current:

- The tag and the digest of the Python base image in the `Dockerfile`.
- The pinned PyPI packages in `requirements.txt`. In the same pull request,
  Renovate regenerates `requirements.lock`.
- All packages in `requirements.lock`. Each Monday, Renovate refreshes the
  lock (`lockFileMaintenance`).
- The GitHub Actions in `.github/workflows/`. Each action has a commit SHA
  and a version comment.

Renovate proposes a new version only after it is 3 days old. For images,
this rule applies only if the registry gives a timestamp. Docker Hub gives
tag timestamps to anonymous clients only for the first 1000 tags.
`library/python` has more than 4000 tags. Thus, a rule that needs a
timestamp blocks each Python digest update. The Monday lock refresh does not
wait. It takes the newest version of each package.

| Update | What occurs |
| --- | --- |
| Digest, patch and pin updates of the base image and the PyPI packages, and the Monday lock refresh | Renovate merges the pull request after the `Test` workflow passes. Then `auto-release.yml` creates a patch release. |
| Minor and major updates | The pull request waits for a person. |
| GitHub Actions updates | Renovate puts all of them in one pull request, "GitHub Actions". This pull request always waits for a person, because new action code runs with `packages: write`. |

`platformAutomerge` is `false`. Thus, Renovate merges the pull request
itself after the checks pass. It does not use GitHub auto-merge, for two
reasons:

- GitHub auto-merge is off for this repository.
- `main` has no required checks. Thus, GitHub auto-merge can merge before CI
  completes.

Four places name the Python minor version, `3.15`:

- The two `FROM` tags in the `Dockerfile`.
- The `python-version` in `.github/workflows/test.yml`.
- The header of `requirements.lock`.

A new Python minor version comes as one "Python version" pull request for
these four places. This pull request waits for a person. Renovate applies
the 3-day age to each file separately. Thus, the pull request can open with
only some of the files. A test fails until all four places name the
same version. Merge the pull request after the `Test` workflow passes. The
next Monday lock refresh recompiles `requirements.lock` on the new Python.
Renovate does not update the Python major version. A person changes it by
hand.

Renovate gets vulnerability data from OSV (`osvVulnerabilityAlerts`) and from
the GitHub Dependabot alerts. If a package in `requirements.lock` has a known
vulnerability, Renovate opens a fix pull request at its next run. This pull
request has the label `security`. It does not wait for the 3-day age. The
automerge rules in the table also apply to it.

## Conventions

This repository has no `CONVENTIONS.md` or `STANDARDS.md`. Use these
sources:

- The [README](README.md) describes the configuration, the renewal, the
  health check and the tests. If your change affects this behavior, update
  the README in the same pull request.
- The `description` fields in `renovate.json` give the reason for each
  Renovate rule.
- The comments in `.github/workflows/` tell how the release workflows work
  together.
- The readiness probe and the alert rule belong to the deployment
  repository. See [Health and monitoring](README.md#health-and-monitoring).

## Documentation

Write all documentation in ASD-STE100 Simplified Technical English (STE).
This section is the same in all repositories of the `coderpunch`
organization. The [style guide](https://github.com/coderpunch/h3xinfra/blob/main/docs/style/STYLE.md) gives more examples
and the full rules of the checker.

### The seven rules

These are the rules of the owner, word for word:

1. Write short sentences. Use a maximum of 20 words for an instruction and 25
   words for a description.
2. Give one instruction in each sentence.
3. Use the active voice.
4. Use the simple tenses: present, past, and future.
5. Do not use the -ing form of a verb.
6. Use one word for one meaning. Do not use a second word for the same thing.
7. Names of APIs, headers, fields, and products stay as they are.

### How to apply the rules

- **Frozen text.** Do not change code blocks, inline code spans, commands,
  configuration snippets, URLs, link targets, quoted output or headings.
  Keep all facts: numbers, versions, dates, IDs, paths, causes and
  decisions. The rules do not apply to frozen text.
- **Instruction or description.** An instruction tells the reader to do
  something. It starts with a verb, with "Do not", or with a short
  condition and then a verb: "If the check fails, stop." All other
  sentences are descriptions.
- **Word count.** A word has a letter or a digit. An inline code span, a
  URL and a quoted string count as one word each. A word with a hyphen or
  a slash is one word.
- **Lists and tables.** Each list item and each table cell is a separate
  unit. Use a numbered list for steps, with one instruction in each step.
  Make a list from a series of more than four items.
- **One instruction.** Split "Do X, then do Y" and "Do X and do Y" into two
  sentences. A condition and one action is one instruction.
- **Active voice.** Name the actor: you, the owner, Renovate, CI, the
  playbook, Terraform, Argo CD, the controller or kubelet. If you do not
  know the actor, do not guess. Make the event the subject: "The pod
  restarted." A state is correct: "The volume is degraded."
- **Tenses.** Use the present tense for descriptions and rules. Use the past
  tense for events and in dated records. Use "will" for a result of an
  instruction. Do not write "is running", "has been" or "have done".
- **The -ing form.** Write "the current version", not "the existing
  version". Write "before you apply", not "before applying". Technical
  names and nouns are correct, for example "networking", "logging",
  "setting", "warning" and "during".
- **The reader and the owner.** Write "you" for the reader. Write "the
  owner" for the person who owns and runs this infrastructure. Do not
  write "we".
- **Maintained documents and dated records.** A `README.md`, a runbook or a
  guide tells the current state. A file under `docs/records/`, or a file
  with a date in its name, is a dated record. In a dated record, change
  only the language. Keep the names and the facts of that time.
- **Notices.** Start a notice with WARNING (data loss or a security risk),
  CAUTION (an outage) or NOTE (useful information). Put it before the step.

### Check your text

Run `ste_check.py` on each document that you change. The script uses only
the Python 3 standard library. It does not change files.

```bash
python3 ste_check.py README.md
python3 ste_check.py --summary docs/
```

The checker uses simple patterns. It can miss a problem, and it can flag
correct text. Fix each finding, or make sure that the text is correct.
Then compare your change with `git diff --word-diff`. Make sure that no
fact, code span, link target or heading changed.

### Glossary

Use the word in the "Use" column. Do not use the words in the "Do not use"
column. Some words are wrong only in one meaning. The "Do not use" column
shows them after "in this meaning". The checker does not flag these words.
You must decide.

<!-- ste-check off -->
#### People

| Use | Meaning | Do not use | Notes |
| --- | --- | --- | --- |
| **you** | The reader of the document. | in this meaning: the reader, one (as a pronoun) | In decapcms-gateway, "the reader" is the report reader of that application. Keep it. |
| **the owner** | The person who owns and runs this infrastructure and the coderpunch repositories. | we, our; in this meaning: the user, the operator, the admin, the administrator, us | Keep "user" for a person who signs in to an application. Keep "operator" for a Kubernetes operator. Keep "admin" in role and console names. In a dated record, do not guess who did an action. |
| **user** | A person who signs in to an application, for example Keycloak, Decap CMS, Open WebUI or Grafana. | end user, end users, end-user, end-users | - |

#### Computers

| Use | Meaning | Do not use | Notes |
| --- | --- | --- | --- |
| **node** | A computer in the k3s cluster. | in this meaning: host, server, machine, box | Keep "machine check" (a CPU error report). |
| **control-plane node** | A node in the `server` inventory group. It runs the k3s server, etcd and the API server. | master node, master nodes; in this meaning: server node, server, master | Keep "k3s server" for the k3s process and role. Keep "master" in the Keycloak "master realm". |
| **agent node** | A node in the `agent` inventory group. It runs the k3s agent and the workloads. | worker node, worker nodes; in this meaning: worker, workers | - |
| **host** | An entry in the Ansible inventory: a node or the virtual `k8s` host. Also in fixed terms: hostname, host key, hostPath, host network, host firewall. | in this meaning: host (for a cluster computer: use node) | - |
| **Ansible controller** | The computer that runs Ansible and Terraform for the cluster, normally the devcontainer. | control node; in this meaning: controller (alone), workstation | Keep "controller" alone for a Kubernetes controller. The workstation of the owner is a different computer. |

#### Repositories and GitHub

| Use | Meaning | Do not use | Notes |
| --- | --- | --- | --- |
| **repository** | A Git repository. | repo, repos | - |
| **pull request** | A GitHub pull request. | PR, PRs, merge request, MR | - |
| **organization** | The GitHub organization `coderpunch`. | org, orgs | - |
| **GitHub Actions** | The CI service of GitHub. | GHA; in this meaning: Actions (alone) | - |
| **pass** | A check or a test gives the expected result. | green; in this meaning: OK, succeed | Keep "succeed" for a command or an operation. |

#### Kubernetes and the stack

| Use | Meaning | Do not use | Notes |
| --- | --- | --- | --- |
| **Kubernetes** | The container platform. The cluster runs k3s. | K8s, k8s, kube | Write the virtual Ansible host as a code span: `k8s`. |
| **namespace** | A Kubernetes namespace. | in this meaning: ns | Keep "ns" for nanoseconds. |
| **Secret** | A Kubernetes Secret object. Write it with a capital S. | secret object, secret objects, Kubernetes secret, Kubernetes secrets | - |
| **secret** | A sensitive value: a password, a token or a private key. | in this meaning: credential (for one value) | Keep "credentials" for a user name together with its password or token. |
| **Service** | A Kubernetes Service object. Write it with a capital S. | in this meaning: service (for an application) | Keep lowercase "service" for a systemd service, for example `k3s-agent.service`. |
| **application** | Software that the cluster runs for users, for example Plex, Mailu or Open WebUI. | app, apps | Keep "GitHub App" (a product name), the Argo CD `Application` kind and paths such as `apps/`. |
| **image** | An OCI container image. | container image, container images, Docker image, Docker images, docker image | Keep "engine image" (a Longhorn name). |
| **chart** | A Helm chart. | Helm package, Helm packages | - |
| **bespoke chart** | A Helm chart that a repository of the organization contains (`h3xinfra-*`). | custom chart, custom charts, custom Helm chart, custom Helm charts, local chart, local charts, local Helm charts | Keep "wrapper chart" and "umbrella chart" for those chart patterns. |
| **upstream chart** | A Helm chart that an external project publishes. | external chart, external charts, external Helm chart, third-party chart, third-party charts | - |
| **release** | A Helm release: one installed copy of a chart in a namespace. Also a GitHub release object. | in this meaning: release (for a version number: use version) | - |
| **version** | A numbered state of software, a chart or an image, for example k3s 1.37.2. | in this meaning: release, build | - |
| **layer** | One numbered unit of the stack: a playbook directory `playbooks/<NN>-<name>/` or a Terraform root module `terraform/layers/<NN>-<name>/`. | in this meaning: module, tier, component | Keep "module" for a Terraform module. |
| **stack** | All layers, in the order that `playbooks/stack-standup.yml` deploys them. Also "dual stack" (IPv4 and IPv6). | - | - |
| **playbook** | An Ansible YAML file that you give to `ansible-playbook`. | in this meaning: play, script | Keep "play" for one play inside a playbook. Keep "script" for shell and Python scripts. |
| **Argo CD** | The GitOps controller. | ArgoCD, Argo-CD | - |
| **PostgreSQL** | The database. | Postgres, PG | - |
| **CNPG** | The CloudNativePG operator and its PostgreSQL `Cluster` objects. | in this meaning: CloudNativePG | Write "CloudNativePG (CNPG)" only at the first mention in a document. |
| **VIP** | A LoadBalancer IP address that MetalLB announces. | LB IP, LB IPs, virtual IP, virtual IPs | - |
| **Gateway** | The shared Gateway API object `h3xinfra-gateway-pre-shared`. All application routes attach to it. | in this meaning: ingress (for the Gateway), proxy | "Envoy Gateway" is the controller product. In decapcms-gateway, "the gateway" is that application. |

#### Actions

| Use | Meaning | Do not use | Notes |
| --- | --- | --- | --- |
| **deploy** | Put a change into the live cluster or onto the nodes. Noun: deployment. | roll out, rolls out, rolled out, ship, ships, shipped, push out; in this meaning: apply, install | Keep "apply" for `terraform apply`, `kubectl apply` and server-side apply. Keep "install" for packages, tools and files. For "the chart ships X", write "the chart contains X". |
| **rollout** | A step-by-step deployment of one change to many nodes or workloads. Also a Kubernetes workload rollout (`kubectl rollout`). | roll-out, roll-outs | - |
| **run** | Start a command, a playbook, a script or a job. | execute, executes, executed, invoke, invokes, invoked, kick off; in this meaning: execution, invocation | Keep "remote code execution" and the systemd "invocation ID". |
| **start** | Make a process, a service or a job begin. | launch, launches, launched, spin up, spins up, fire up, bring up, boot up | Keep "boot" for the operating system of a node. |
| **stop** | Make a process, a service or a job end. | halt, halts, halted; in this meaning: terminate, kill | Keep "kill" for signals (SIGKILL) and "Terminating" for the pod state. Keep "shut down" for the power-off of a node. |
| **reboot** | Stop and start the operating system of a node. | in this meaning: restart (for a node) | Keep "power-cycle" for a cut of AC power. |
| **restart** | Stop and start a process, a service or a pod. | bounce, bounces, bounced; in this meaning: reboot (for a process) | - |
| **delete** | Destroy an object, a file or data. After this, the item does not exist. | wipe, wipes, wiped, erase, erases, erased, nuke, get rid of; in this meaning: purge, destroy, drop | Keep "purge" for the Longhorn snapshot purge and "destroy" for `terraform destroy`. |
| **remove** | Take an item out of a configuration, a list, the code or a node. This does not delete data. | strip out, take out; in this meaning: drop | Keep "drop" for network packets and Linux capabilities. |
| **configure** | Give settings to software. | set up, sets up | - |
| **configuration** | The settings of software, as a whole. | config, setup; in this meaning: settings (for the whole configuration) | Write a volume, a key or a file named config as a code span: `config`. |
| **make sure** | Do what is necessary so that a condition is true. | ensure, ensures, ensured, assure, assures | - |
| **check** | Look at something to find its state. Also a CI check or a test check. | examine, examines, examined, inspect, inspects, inspected, double-check; in this meaning: validate, validation | Keep "validate" in technical names: `terraform validate`, admission validation, schema validation. |
| **verify** | Check and get proof that something is correct. "Verified" means that the check passed. Also TLS, signature and checksum verification. | in this meaning: confirm, confirmed | Keep "confirm" for the `confirm_destroy` prompt. |
| **update** | Change to a newer version, or change content to the current state. | bump, bumps, bumped; in this meaning: upgrade | Keep "upgrade" in named operations: `apt upgrade`, `helm upgrade`, the Longhorn engine upgrade. |
| **change** | Make something different. | modify, modifies, modified, modification, modifications, alter, alters, altered, tweak, tweaks, tweaked; in this meaning: edit, adjust | Keep "edit" for a change to the text of a file or a CMS entry. |
| **use** | Do work with a tool, a method or a value. | utilize, utilizes, utilized, utilise, leverage, leverages, employ, employs, make use of | - |
| **get** | Come to have something. | obtain, obtains, obtained, retrieve, retrieves, retrieved; in this meaning: acquire, fetch | Keep "acquire" for a lock and "fetch" for `git fetch` and HTTP requests. |
| **fix** | Make a bug, a fault or a problem go away. | remediate, remediates, remediated; in this meaning: resolve, repair, correct (as a verb), remediation | Keep "resolve" for DNS resolution and the RESOLVED status. |
| **allow** | Give permission for an action or for traffic. | permit, permits, permitted; in this meaning: enable, let | Keep "enable" for a feature switch, for example `enabled: true`. |
| **sign in** | Give credentials to an application to get access. Noun: sign-in. | log in, logs in, logged in, log on, logon; in this meaning: login | Keep "login" for an SSH login name, for example `ansible`, and in product names. |
| **restore** | Put data back from a backup or a snapshot. | in this meaning: recover (for data) | - |
| **recover** | Bring a node, a service or a volume back to normal operation. | in this meaning: restore (for a node or a service), heal | - |

#### States and results

| Use | Meaning | Do not use | Notes |
| --- | --- | --- | --- |
| **retired** | No longer used or deployed. Only the history keeps it. | obsolete; in this meaning: legacy, deprecated, former, decommissioned | Keep "legacy" in technical names (legacy BIOS) and "deprecated" for an upstream deprecation. |
| **problem** | Something that does not work as expected. | in this meaning: issue, defect | Keep "issue" for a GitHub issue. Use "bug" for a defect in software and "fault" for a defect in hardware. |
| **alert** | A Prometheus or Alertmanager alert. | alarm, alarms | - |

#### Documents

| Use | Meaning | Do not use | Notes |
| --- | --- | --- | --- |
| **directory** | A directory in a file system or a repository. | dir, dirs; in this meaning: folder | Keep "folder" for a Decap CMS media folder. |
| **documentation** | Text that tells how the system works or what to do. One file is a document. | doc, docs | Write the `docs/` directory as a code span. |
| **environment variable** | A variable in the environment of a process. | env var, env vars, envvar | - |
| **authentication** | Proof of who a user or a client is. | auth, authn, AuthN | - |
| **authorization** | The decision about what a user or a client can do. | authz, AuthZ | - |
| **certificate** | An X.509 certificate. | cert, certs | - |

#### Small words

| Use | Meaning | Do not use | Notes |
| --- | --- | --- | --- |
| **must** | An obligation. | have to, has to, need to, needs to, is required to, are required to, should | For an expected result, use the present or the future tense: "The command returns 0." |
| **because** | A cause. | due to, owing to; in this meaning: since (as a cause), as (as a cause) | Keep "since" for time, for example "since 2026-10-04". |
| **thus** | A result. | therefore, hence, consequently, accordingly; in this meaning: so (as a result) | For a purpose, write "to", not "so that" or "in order to". |
| **to** | A purpose. | in order to; in this meaning: so that | - |
| **for example** | One or more examples. | e.g., for instance; in this meaning: such as | - |
| **that is** | The same thing in different words. | i.e. | - |
| **and other** | The list continues. Better: give the full list. | etc., and so on | - |
| **but** | A contrast. | however, although, though, whereas, nevertheless, nonetheless | - |
| **also** | An addition. | additionally, in addition, furthermore, moreover | - |
| **if** | A condition. | in case, provided that, in the event that | - |
| **after** | Later than an event. | once, subsequently | For "once" in the meaning "one time", write "one time". |
| **before** | Earlier than an event. | prior to | - |
| **about** | On the topic of. | regarding, concerning, with respect to, with regard to, in terms of | - |
| **approximately** | Near a quantity, but not exact. | roughly, circa, approx., about + number, around + number | "~" is correct in table cells and code only. |
| **through** | By means of a path, a tool or a step. | via | - |
<!-- ste-check on -->
