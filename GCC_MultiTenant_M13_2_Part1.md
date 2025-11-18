# Module 13: Scale & Performance Optimization
## Video 13.2: Auto-Scaling Multi-Tenant Infrastructure (Enhanced with TVH Framework v2.0)

**Duration:** 35 minutes
**Track:** GCC Multi-Tenant Architecture for RAG Systems
**Level:** Builds on M11-M13.1
**Audience:** Platform engineers managing 50+ tenant GCC RAG deployments
**Prerequisites:** 
- GCC Multi-Tenant M11-M13.1 (Tenant isolation, rate limiting, performance patterns)
- Kubernetes fundamentals (pods, deployments, services)
- Horizontal Pod Autoscaler (HPA) basics
- Prometheus metrics and custom metrics API

---

## SECTION 1: INTRODUCTION & HOOK (2-3 minutes, 400-500 words)

**[0:00-0:30] Hook - The GCC Scale Crisis**

[SLIDE: Title - "Auto-Scaling Multi-Tenant Infrastructure"]

**NARRATION:**
"It's 2:47 AM in Bangalore. Your GCC platform serves 52 tenants across media, finance, and retail verticals. Everything was fine at 11 PM when you went to bed. But right now, a major sporting event just finished in the US, and 8 media tenants are suddenly processing 50 times their normal traffic—journalists frantically querying RAG systems for match statistics, player histories, and real-time commentary generation.

Your platform has a problem. You provisioned for average load, not peak. Those 8 tenants are crushing your shared infrastructure. Pods are maxed out. Query latency has spiked from 200ms to 12 seconds. But here's the worst part: it's not just the media tenants suffering. Your 44 OTHER tenants—banks running risk analyses, retailers processing inventory queries—they're all experiencing slowdowns too because they share the same pod pool.

Your phone starts buzzing. Finance tenant escalations. Retail SLA breaches. The platform team lead messages: 'Why didn't we auto-scale? We have HPA configured!' You remote in and discover the truth: your HPA is scaling based on GLOBAL CPU metrics. It sees 'cluster CPU at 75%, acceptable' while individual pods serving media tenants are pegged at 100%. The system doesn't know there's a localized crisis.

By 4 AM, you've manually scaled up, incident resolved, but the damage is done. Three tenants are threatening to move to dedicated infrastructure. Your CFO wants answers: 'We built a shared platform to save money. If we have to over-provision for worst-case scenarios, what's the point?'

The driving question: How do you build auto-scaling that responds to TENANT-SPECIFIC load patterns, prevents noisy neighbors from affecting others, yet still delivers the cost efficiency that justifies a multi-tenant architecture?"

**INSTRUCTOR GUIDANCE:**
- Emphasize the multi-tenant complexity: one tenant's spike affects everyone
- Highlight the failure of naive auto-scaling (global metrics blind to tenant isolation)
- Set up the tension: cost efficiency vs. performance isolation
- Make it visceral: this is a career-defining incident for platform engineers

---

**[0:30-1:30] What We're Building Today**

[SLIDE: Kubernetes Multi-Tenant Auto-Scaling Architecture showing:
- Kubernetes cluster with HPA controller
- Per-tenant queue depth metrics (Prometheus)
- Resource quotas preventing monopoly
- Pod anti-affinity rules for distribution
- Scale-up trigger: queue_depth > 10 per tenant
- Scale range: 3 minimum → 20 maximum pods]

**NARRATION:**
"Today, we're building a production-grade Kubernetes auto-scaling system for multi-tenant RAG infrastructure. Not a toy example—this is what runs in Indian GCCs managing billions of rupees in infrastructure.

Here's what this system will do:

**First**, it scales based on PER-TENANT queue depth metrics, not global CPU. When media tenants spike, we scale pods to handle THEIR load without over-provisioning for everyone.

**Second**, it enforces resource quotas at the pod level. Even if we scale from 3 to 20 pods for a traffic spike, no single tenant can consume more than 30% of cluster resources. Performance isolation guaranteed.

**Third**, it implements tenant-aware load balancing with affinity rules. Media tenant queries route to pods already handling media data (cache locality), but we use anti-affinity to prevent all media pods from landing on the same node (blast radius containment).

**Fourth**, it responds within 2 minutes of load spikes and gracefully scales down when traffic normalizes, minimizing cost while maintaining SLAs.

By the end of this video, you'll have a Kubernetes HPA configuration with custom metrics that scales multi-tenant RAG infrastructure intelligently, prevents noisy neighbor problems, and delivers the 40-60% cost savings that justify shared platforms—without the 3 AM incidents."

**INSTRUCTOR GUIDANCE:**
- Show the complete architecture visually—learners need to see the system holistically
- Emphasize the quantified outcomes: 2-minute scale response, 30% resource cap per tenant
- Connect to GCC economics: this is why GCCs choose multi-tenant over dedicated
- Preview the working code: this is production-ready, not academic

---

**[1:30-2:30] Learning Objectives**

[SLIDE: Learning Objectives (4 bullet points)]

**NARRATION:**
"In this video, you'll learn:

1. **Implement Horizontal Pod Autoscaler (HPA) with custom per-tenant metrics** - Scale pods based on tenant-specific queue depth, not naive global CPU metrics, responding to localized load spikes within 2 minutes.

2. **Design resource quotas and LimitRanges to prevent tenant monopoly** - Enforce hard caps on CPU/memory per tenant at the pod level, ensuring no single tenant consumes more than 30% of cluster resources even during scale-up.

3. **Build tenant-aware load balancing with affinity and anti-affinity rules** - Route requests to pods with cache locality while distributing pods across nodes for fault tolerance, maintaining sub-100ms latency for cache hits.

4. **Create graceful scale-down strategies that preserve tenant SLAs** - Scale down from 20 pods to 3 when load normalizes without dropping active queries, using connection draining and graceful termination periods.

These aren't generic Kubernetes skills. This is GCC-specific multi-tenant auto-scaling that balances cost efficiency, performance isolation, and operational resilience—skills worth a 30-40% salary premium in platform engineering roles."

**INSTRUCTOR GUIDANCE:**
- Each objective specifies the measurable outcome (2 minutes, 30%, sub-100ms)
- Emphasize the GCC context: this solves real problems Indian platform teams face
- Connect to career value: these skills differentiate senior from staff engineers

---

## SECTION 2: CONCEPTUAL FOUNDATION (8-10 minutes, 1,500-2,000 words)

**[2:30-4:00] The Multi-Tenant Auto-Scaling Challenge**

[SLIDE: Problem visualization showing:
- Traditional single-tenant: dedicated resources per app
- Naive multi-tenant: shared pool, no tenant awareness
- Intelligent multi-tenant: per-tenant metrics with quotas]

**NARRATION:**
"Let's understand why multi-tenant auto-scaling is fundamentally different from single-tenant scaling.

In a traditional single-tenant RAG system, auto-scaling is straightforward. You have one application, one set of pods, one traffic pattern. When CPU hits 70%, you scale up. When it drops to 40%, you scale down. Done. The application owns its resources, and scaling decisions are binary: am I overloaded? Yes? Add pods.

But in a multi-tenant GCC platform serving 50+ business units, this naive approach creates three critical failures:

**Failure #1: The Noisy Neighbor Problem**

Imagine your platform serves 50 tenants. 48 tenants are running at normal load—5 queries per second each. But 2 tenants—let's say media companies—are experiencing a 10× spike because of breaking news. They're now doing 50 queries per second.

With global CPU-based auto-scaling, here's what happens: The cluster CPU rises from 60% to 72%. HPA sees this and says, 'We're at 72%, above the 70% threshold. Scale up by 1 pod.' You go from 10 pods to 11 pods. Great, right?

Wrong. Those 2 media tenants are still monopolizing resources. The extra pod gets immediately saturated with media queries because the load balancer has no tenant awareness. The 48 normal tenants are STILL suffering because they're competing for CPU on pods dominated by media traffic. You've added capacity, but you haven't solved the isolation problem.

**Failure #2: The Over-Provisioning Trap**

Okay, so maybe you learn from failure #1. You say, 'Fine, let's set the HPA threshold lower—scale up at 60% CPU to keep headroom.' Now you're scaling aggressively. The problem? 90% of the time, you're over-provisioned. Those media spikes happen 2-3 times per week for 2-4 hours. The rest of the time, you're running 15 pods when 8 would suffice.

Your CFO sees the bill: 'We're paying ₹30 lakh per month for infrastructure. If we provision for peak, we could have just given each tenant dedicated resources for ₹25 lakh and avoided the multi-tenant complexity entirely. What's the point?'

You've built a multi-tenant platform that costs MORE than dedicated infrastructure because you're over-provisioning to handle the noisy neighbor problem. That's the trap.

**Failure #3: The Delayed Response Problem**

Even if you fix tenant isolation, there's a timing problem. HPA makes scaling decisions based on metric averages over a time window—typically 30 seconds to 1 minute. For a sudden 10× traffic spike, this means:
- **T+0 seconds**: Media tenant spike begins, queries start queuing
- **T+30 seconds**: Metrics aggregator reports high queue depth
- **T+60 seconds**: HPA observes sustained high metric, decides to scale
- **T+90 seconds**: Kubernetes scheduler provisions new pod
- **T+120 seconds**: Pod becomes ready, starts accepting traffic

That's a 2-minute delay from spike to resolution. During those 2 minutes, query latency for media tenants has spiked from 200ms to 8-12 seconds. For real-time journalism or trading systems, that's unacceptable.

**The Solution: Per-Tenant Metrics with Resource Quotas**

Here's the intelligent approach we're building today:

**Component #1: Per-Tenant Queue Depth Metrics**

Instead of scaling on global CPU, we track queue depth (number of pending queries) per tenant. This gives us tenant-specific visibility:
- Media tenant 1: 45 queries queued (spike detected)
- Media tenant 2: 52 queries queued (spike detected)
- Finance tenant: 3 queries queued (normal)
- Retail tenant: 1 query queued (normal)

We configure HPA to scale when the AVERAGE queue depth per tenant exceeds 10. This means we're not over-provisioning for the entire cluster—we're scaling just enough to clear the backlog for affected tenants.

**Component #2: Resource Quotas (Pod-Level Caps)**

Even if we scale up to 20 pods, we enforce resource quotas: no tenant can consume more than 30% of total cluster CPU/memory. This is implemented via Kubernetes LimitRanges and admission controllers.

Result: When media tenants spike, they get the extra pods they need, but they can't monopolize the cluster. Finance and retail tenants still have guaranteed minimum resources (20% of cluster each, as per their SLA tier).

**Component #3: Tenant-Aware Load Balancing**

We use pod affinity rules to route media tenant queries to pods already handling media data (cache locality benefits). But we use anti-affinity rules to ensure those pods are distributed across multiple nodes (no single point of failure). When we scale up, new pods inherit these affinity rules automatically.

**Component #4: Graceful Scale-Down**

When the spike ends and queue depth drops below 5 per tenant, HPA begins scale-down. But we don't just kill pods. We:
- Stop sending new requests to the pod (remove from load balancer)
- Allow existing requests to complete (30-second drain period)
- Terminate pod gracefully (SIGTERM, not SIGKILL)

This prevents the '3:47 AM false alarm' scenario where scale-down causes query failures and wakes up the on-call engineer.

**The Economics**

Here's why this matters for GCC platform teams:

With naive auto-scaling (over-provisioned):
- Average: 15 pods × ₹2,000/month = ₹30,000/month
- Peak handling: adequate
- Cost efficiency: 40% waste

With per-tenant auto-scaling (this system):
- Average: 8 pods × ₹2,000/month = ₹16,000/month (normal load)
- Peak: scales to 18 pods for 8 hours/week = +₹6,000/month (4 extra hours × 4 times/month × ₹150/pod-hour)
- Total: ₹22,000/month
- **Savings: ₹96,000/year (32% reduction) while maintaining same SLAs**

For a 50-tenant GCC platform, that's ₹48 lakh in annual infrastructure savings. That's the difference between a platform that justifies its existence and one that gets shut down in favor of dedicated tenant resources."

**INSTRUCTOR GUIDANCE:**
- Use concrete numbers (50 tenants, 10× spike, 2-minute delay) to make it tangible
- Emphasize the economic argument: this isn't academic, it's how GCCs justify shared platforms
- Show the failure modes first, then introduce the solution as a response to each failure
- Connect to learner's journey: they've built tenant isolation (M11), rate limiting (M12), now they're adding intelligent scaling

---

**[4:00-6:30] Horizontal Pod Autoscaler (HPA) Architecture**

[SLIDE: Kubernetes HPA Control Loop showing:
- Metrics Server collecting pod resource usage
- Custom Metrics API (Prometheus adapter)
- HPA Controller evaluating scale decisions
- Deployment Controller executing scale operations
- Feedback loop: new pods → metrics updated → HPA re-evaluates]

**NARRATION:**
"Before we write code, you need to understand how Kubernetes HPA works at an architectural level. This isn't just 'magic Kubernetes automation'—it's a control loop with specific components, decision logic, and failure modes.

**The HPA Control Loop (5-Step Process):**

**Step 1: Metrics Collection**

Every 15 seconds (configurable), the Kubernetes Metrics Server collects resource usage from all pods:
- CPU utilization (from cgroups)
- Memory utilization (from cgroups)
- Custom metrics (from external APIs like Prometheus)

For our multi-tenant system, we're primarily interested in custom metrics: per-tenant queue depth. This is exposed via the Prometheus adapter, which translates Prometheus queries into the Kubernetes Custom Metrics API format.

**Step 2: Metric Aggregation**

HPA fetches the target metric for all pods in the deployment. For example, if we're scaling based on 'queue_depth_per_tenant' and we have 10 pods, HPA queries: 'What's the queue depth for each pod right now?'

It gets back: `[12, 15, 8, 11, 14, 9, 13, 10, 16, 11]` (queue depth across 10 pods).

HPA calculates the average: `(12+15+8+11+14+9+13+10+16+11) / 10 = 11.9 queries per pod average`.

**Step 3: Desired Replicas Calculation**

HPA uses this formula to determine how many replicas (pods) are needed:

```
desiredReplicas = ceil(currentReplicas × (currentMetricValue / targetMetricValue))
```

In our example:
- Current replicas: 10 pods
- Current metric value: 11.9 (average queue depth per pod)
- Target metric value: 10 (configured in HPA spec)

```
desiredReplicas = ceil(10 × (11.9 / 10)) = ceil(10 × 1.19) = ceil(11.9) = 12 pods
```

HPA decides: 'We need 12 pods to bring queue depth down to the target of 10 per pod.'

**Step 4: Scale Decision and Stabilization**

Here's where HPA gets smart to avoid flapping (rapid scale-up/scale-down oscillations):

- **Scale-up stabilization**: HPA uses the HIGHEST metric value from the last 3 minutes (default). If we saw a brief spike 2 minutes ago, HPA remembers and scales up accordingly.
- **Scale-down stabilization**: HPA uses the LOWEST metric value from the last 5 minutes (default). This prevents premature scale-down if load is fluctuating.

In our case, let's say the last 3 minutes of average queue depth was: `[11.9, 13.2, 12.1]`. HPA uses 13.2 (the max) for scale-up decisions. This ensures we don't under-provision if we caught the metric during a temporary dip.

**Step 5: Deployment Update**

HPA updates the Deployment's `spec.replicas` field from 10 to 12. The Deployment Controller sees this change and:
- Schedules 2 new pods
- Kubernetes scheduler finds nodes with available capacity
- Kubelet on those nodes pulls the container image and starts the pods
- Pods pass readiness probe (health check)
- Load balancer adds new pods to rotation

Total time: 30-90 seconds depending on image pull time and readiness probe interval.

**Why Custom Metrics Matter for Multi-Tenancy**

Standard Kubernetes metrics (CPU, memory) don't capture tenant-specific load patterns. Consider:

**Scenario A: Global CPU at 60%, Tenant-Specific Problem**
- 48 tenants running at 2% CPU each (96% of load)
- 2 tenants running at 50% CPU each (4% of load, but saturated)
- Global CPU: 48×2% + 2×50% = 196% / 50 pods = 60% average (no scale-up triggered)
- **Problem**: Those 2 tenants experience 8-second latency while HPA thinks everything is fine.

**Scenario B: Queue Depth at 45 per Affected Tenant**
- Same situation, but we track queue depth per tenant
- HPA sees: Media tenant 1 queue depth = 45, Media tenant 2 queue depth = 52
- Average across all tenants: (45+52+3+2+1+...) / 50 ≈ 12 (above threshold of 10)
- **Result**: HPA scales up immediately, specific to the tenants experiencing load

This is why we're using custom per-tenant queue depth metrics instead of naive CPU-based scaling.

**The Multi-Tenant Metric Challenge**

But there's a subtlety: How do we calculate 'average queue depth per tenant' in a pod-based world?

In our platform, each pod can serve multiple tenants (we don't have dedicated pods per tenant—that would eliminate multi-tenant cost benefits). So the metric 'queue_depth_per_tenant' is actually:

```
queue_depth_per_tenant = total_queued_queries_across_all_pods / number_of_active_tenants
```

For example:
- 10 pods, 50 tenants
- Total queued queries: 450 (summed across all pods)
- Active tenants (sending queries right now): 30 tenants
- **Metric**: 450 / 30 = 15 queries per active tenant (above threshold, scale up)

This metric is exported by our application code (we'll see this in Section 4) and scraped by Prometheus every 15 seconds. The Prometheus adapter exposes it to Kubernetes HPA via the Custom Metrics API.

**HPA Configuration Parameters (What We'll Set)**

When we write our HPA manifest, here are the key parameters:

1. **minReplicas: 3** - Never scale below this (maintain baseline capacity for 50 tenants)
2. **maxReplicas: 20** - Budget ceiling (₹40,000/month max infrastructure cost)
3. **metrics.target.averageValue: 10** - Scale up if queue depth per tenant exceeds 10
4. **behavior.scaleUp.stabilizationWindowSeconds: 60** - Wait 60 seconds before scaling up (avoid flapping)
5. **behavior.scaleDown.stabilizationWindowSeconds: 300** - Wait 5 minutes before scaling down (ensure load is truly gone)
6. **behavior.scaleUp.policies.periodSeconds: 60** - Re-evaluate scale-up every 60 seconds
7. **behavior.scaleUp.policies.value: 4** - Max 4 pods added per scale-up event (avoid resource exhaustion)

These parameters balance responsiveness (2-minute scale-up) with stability (no flapping) and cost control (max 20 pods)."

**INSTRUCTOR GUIDANCE:**
- Walk through the control loop step-by-step—HPA is not magic, it's deterministic logic
- Use concrete numbers (10 pods, 11.9 average, target 10) so learners can trace the math
- Emphasize why custom metrics matter: global CPU misses tenant-specific problems
- Explain stabilization windows: this prevents the '3 AM flapping incident' where HPA scales up/down every 2 minutes
- Connect to Section 4: 'We'll implement the custom metrics exporter that feeds queue depth to Prometheus'

---

**[6:30-9:00] Resource Quotas and Tenant Isolation**

[SLIDE: Kubernetes Resource Management Hierarchy showing:
- Namespace (tenant boundary)
- ResourceQuota (namespace-level caps)
- LimitRange (pod-level defaults and caps)
- Pod spec (individual requests/limits)
- QoS classes (Guaranteed, Burstable, BestEffort)]

**NARRATION:**
"Auto-scaling solves the 'do we have enough pods' problem. But in a multi-tenant system, we also need to solve the 'can one tenant monopolize resources' problem. That's where Kubernetes resource quotas and limit ranges come in.

**The Multi-Tenant Resource Problem**

Let's say we scale from 10 pods to 20 pods because media tenants spiked. Great! But without resource quotas, here's what can happen:

All 20 pods are available. Media tenant queries flood the system. Because the load balancer is naive (round-robin or least-connections), media queries get routed to ALL 20 pods. Now:
- Media tenants are consuming 18 out of 20 pods (90% of cluster capacity)
- Finance tenants are fighting for the remaining 2 pods (10% of cluster capacity)
- Retail tenants can't even get scheduled because the cluster is 'full'

We've scaled up, but we haven't isolated. Finance and retail tenants are still suffering. This is the 'resource monopoly' problem.

**Solution #1: Namespace-Level ResourceQuotas**

In our architecture, each tenant gets their own Kubernetes namespace. For example:
- Namespace: `tenant-media-1`
- Namespace: `tenant-finance-1`
- Namespace: `tenant-retail-1`

We define a ResourceQuota for each namespace that caps total resource usage:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tenant-quota
  namespace: tenant-media-1
spec:
  hard:
    requests.cpu: "6"        # Max 6 CPU cores requested
    requests.memory: "12Gi"  # Max 12GB memory requested
    limits.cpu: "8"          # Max 8 CPU cores limit
    limits.memory: "16Gi"    # Max 16GB memory limit
    pods: "10"               # Max 10 pods in this namespace
```

What this means: Even if we scale the cluster to 100 pods with 40 CPU cores total, `tenant-media-1` can only consume 8 cores max. If they try to schedule an 11th pod, Kubernetes blocks it with: 'Quota exceeded for requests.cpu'.

**The Quota Math for 50 Tenants**

Let's say our cluster has:
- 40 CPU cores total
- 80GB memory total
- 20 pods max (our HPA limit)

We allocate quotas based on tenant SLA tiers:

**Gold Tier (10 tenants): 30% of resources each**
- CPU quota: 40 × 0.30 / 10 = 1.2 cores per tenant
- Memory quota: 80 × 0.30 / 10 = 2.4GB per tenant
- Pods: 20 × 0.30 / 10 = 0.6 pods (round up to 1)

**Silver Tier (20 tenants): 50% of resources**
- CPU quota: 40 × 0.50 / 20 = 1.0 cores per tenant
- Memory quota: 80 × 0.50 / 20 = 2.0GB per tenant
- Pods: 20 × 0.50 / 20 = 0.5 pods (round up to 1)

**Bronze Tier (20 tenants): 20% of resources**
- CPU quota: 40 × 0.20 / 20 = 0.4 cores per tenant
- Memory quota: 80 × 0.20 / 20 = 0.8GB per tenant
- Pods: 20 × 0.20 / 20 = 0.2 pods (round up to 1)

Notice we over-subscribe (30% + 50% + 20% = 100%, but realistically not all tenants max out simultaneously). This is intentional—it's the cost efficiency of multi-tenancy. But the quotas ensure no single tenant can monopolize.

**Solution #2: LimitRange (Pod-Level Defaults)**

ResourceQuotas cap the TOTAL usage per namespace. But what about individual pod specs? Without limits, a developer could deploy a pod with `requests.cpu: 100` and crash the cluster.

LimitRange enforces defaults and maximum values at the pod level:

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: tenant-limits
  namespace: tenant-media-1
spec:
  limits:
  - type: Pod
    max:
      cpu: "4"        # No single pod can request >4 cores
      memory: "8Gi"   # No single pod can request >8GB
    min:
      cpu: "100m"     # Every pod must request >=100 millicores
      memory: "128Mi" # Every pod must request >=128MB
  - type: Container
    default:
      cpu: "500m"     # If container spec omits CPU, default to 500m
      memory: "512Mi" # If container spec omits memory, default to 512Mi
    defaultRequest:
      cpu: "250m"     # Default request (scheduler uses this)
      memory: "256Mi" # Default request
```

This prevents accidents: A developer deploys a pod without specifying resources, and Kubernetes applies the defaults (250m CPU, 256Mi memory). This ensures we don't have 'resource hog' pods.

**How This Combines with HPA**

Here's the complete flow:

1. **Traffic spike detected**: Media tenant queue depth hits 45 queries per tenant (above threshold of 10)
2. **HPA scales up**: Decides to add 5 pods (10 → 15 total in cluster)
3. **Resource quota check**: Kubernetes checks if `tenant-media-1` namespace has quota for 5 more pods
   - Current usage: 3 pods consuming 1.5 CPU cores, 3GB memory
   - Quota: 8 CPU cores, 16GB memory, 10 pods max
   - **Result**: Quota allows (3+5=8 pods, well under limit)
4. **LimitRange applied**: Each new pod inherits default resource requests (250m CPU, 256Mi memory)
5. **Pods scheduled**: Kubernetes scheduler places pods on nodes with available capacity
6. **Load balanced**: New pods start accepting media tenant traffic
7. **Queue depth drops**: Within 2 minutes, queue depth falls to 8 per tenant (below threshold)

But critically, even though we scaled up to 15 pods, `tenant-media-1` is still capped at 8 CPU cores total by the ResourceQuota. Other tenants' quotas are unaffected. Isolation maintained.

**The Anti-Pattern: No Quotas**

What happens without quotas? Real incident from a GCC in Pune (2023):

- Platform served 40 tenants, no resource quotas configured
- One retail tenant deployed an experimental ML model (CPU-intensive embeddings)
- The model was inefficient: 8 CPU cores per pod (!)
- Retail tenant scaled to 5 pods = 40 CPU cores (entire cluster)
- **Result**: 39 other tenants experienced complete outage for 4 hours
- **Cost**: ₹12 lakh in SLA penalties, 2 tenants churned to competitors

After this incident, they implemented ResourceQuotas with a 'no single tenant >30% cluster resources' policy. Problem solved.

**Practical Quota Management**

In production GCC platforms, quotas are managed dynamically:

- **Initial allocation**: Based on tenant SLA tier (Gold/Silver/Bronze)
- **Quarterly review**: Platform team reviews actual usage, adjusts quotas
- **Burst allocation**: Tenants can request temporary quota increases (e.g., 'We're launching a new product, expect 3× traffic for 2 weeks')
- **Cost tracking**: Quota usage feeds into chargeback model (see M13.3)

This isn't set-and-forget. It's active resource governance."

**INSTRUCTOR GUIDANCE:**
- Use concrete numbers (40 CPU cores, 80GB memory, 50 tenants) to make quota math tangible
- Explain the over-subscription strategy: why 100% allocation works (not all tenants max out simultaneously)
- Show the real incident (Pune GCC outage): this is why quotas aren't optional
- Connect to HPA: quotas prevent monopoly, HPA adds capacity, together they solve multi-tenant scaling
- Preview Section 4: 'We'll write the ResourceQuota and LimitRange manifests'

---

**[9:00-10:30] Tenant-Aware Load Balancing and Affinity**

[SLIDE: Pod Affinity Strategies showing:
- Affinity: prefer pods on same node (cache locality)
- Anti-affinity: require pods on different nodes (fault tolerance)
- Tenant affinity: route queries to pods with tenant data cached
- Topology spread: distribute pods across availability zones]

**NARRATION:**
"We've solved the 'how many pods' problem (HPA) and the 'no monopoly' problem (quotas). Now we need to solve the 'which pod handles which query' problem. This is tenant-aware load balancing.

**The Cache Locality Problem**

In a RAG system, embeddings and vector data are cached in-memory on each pod for performance. For example:
- Pod A has cached embeddings for media tenant 1 (50MB in RAM)
- Pod B has cached embeddings for finance tenant 1 (30MB in RAM)
- Pod C has cached embeddings for retail tenant 1 (40MB in RAM)

If a media tenant 1 query arrives at Pod B, we have a cache miss. Pod B must:
1. Fetch embeddings from the vector database (network latency: 20ms)
2. Load embeddings into memory (compute time: 15ms)
3. Process the query (compute time: 50ms)
**Total latency: 85ms**

If the same query arrived at Pod A (which already has media tenant 1 embeddings cached):
1. Use cached embeddings (no fetch)
2. Process the query (compute time: 50ms)
**Total latency: 50ms**

That's a 41% latency improvement from cache locality. At scale, this matters: 85ms × 10,000 queries/second = 850 seconds of compute time vs. 50ms × 10,000 = 500 seconds. That's a 40% efficiency gain.

**Solution #1: Tenant Affinity (Sticky Sessions)**

We use Kubernetes Service with session affinity to route queries from the same tenant to the same pod:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: rag-service
spec:
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 3600  # 1-hour session stickiness
  selector:
    app: rag-service
  ports:
  - port: 8000
    targetPort: 8000
```

Now, queries from media tenant 1 (identified by source IP or tenant ID header) route to the same pod for 1 hour, maximizing cache hits.

**But Wait—What About Scaling?**

Here's the tension: Session affinity works great when we have 10 stable pods. But when HPA scales from 10 to 15 pods, new pods have EMPTY caches. If we route traffic to them immediately, we get cache misses and latency spikes.

**Solution #2: Weighted Load Balancing with Warm-Up**

When a new pod starts, we mark it as 'warming up' for the first 5 minutes:

```python
# In FastAPI application code
@app.on_event("startup")
async def startup_event():
    # Mark pod as warming up
    redis.setex(f"pod:{POD_IP}:warming_up", 300, "true")  # 5-minute TTL
    
    # Pre-load embeddings for top 5 active tenants
    top_tenants = get_top_active_tenants(limit=5)
    for tenant_id in top_tenants:
        load_tenant_embeddings(tenant_id)  # Pre-cache
    
    # After 5 minutes, mark pod as ready for full traffic
    await asyncio.sleep(300)
    redis.delete(f"pod:{POD_IP}:warming_up")
```

Our load balancer (e.g., Envoy proxy or Nginx) checks this Redis flag and sends only 20% of normal traffic to warming-up pods. After 5 minutes, the pod is 'hot' and receives full traffic.

**Result**: New pods during scale-up don't cause latency spikes. We trade a 5-minute warm-up period for consistent performance.

**Solution #3: Anti-Affinity for Fault Tolerance**

But there's a blast radius problem: If all media tenant pods land on the same physical node, and that node fails, ALL media tenants experience an outage simultaneously.

We use pod anti-affinity to force Kubernetes to spread pods across nodes:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-service
spec:
  replicas: 10
  template:
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - rag-service
            topologyKey: kubernetes.io/hostname  # Force different nodes
```

This says: 'When scheduling a `rag-service` pod, Kubernetes MUST place it on a node that doesn't already have another `rag-service` pod.' 

**The Trade-off**: If we have 10 nodes and scale to 15 pods, 5 pods will be 'pending' until we add more nodes. This forces us to also auto-scale the Kubernetes cluster itself (using Cluster Autoscaler or Karpenter). That's outside the scope of this video, but it's a real constraint.

In GCC environments, we typically:
- Over-provision nodes by 20% (e.g., 12 nodes for 10 pods) to allow headroom for anti-affinity
- Use Cluster Autoscaler to add nodes when pod scheduling fails due to anti-affinity constraints
- Set HPA maxReplicas conservatively to avoid node exhaustion

**Solution #4: Topology Spread Constraints (Advanced)**

For truly critical tenants (e.g., Gold SLA), we use topology spread constraints to distribute their queries across availability zones:

```yaml
topologySpreadConstraints:
- maxSkew: 1
  topologyKey: topology.kubernetes.io/zone
  whenUnsatisfiable: DoNotSchedule
  labelSelector:
    matchLabels:
      tenant-tier: gold
```

This ensures: 'Gold tenant pods must be spread across availability zones with a maximum skew of 1.' Meaning if we have 3 zones, we can't have 5 pods in zone A, 5 in zone B, and 0 in zone C. We must have 4-4-2 or 5-4-1 at most.

**Why This Matters**: If an entire availability zone fails (rare but happens—AWS us-east-1 outage in 2023), Gold tenants still have pods running in the other 2 zones. Bronze tenants might all be in one zone (acceptable risk for their SLA tier).

**The Complete Load Balancing Flow**

1. **Query arrives** from media tenant 1 with header `X-Tenant-ID: media-1`
2. **Service session affinity** routes to Pod 7 (media tenant 1's cached pod)
3. **Pod 7 is warming up** (recently scaled up): load balancer sees Redis flag, routes only 20% of queries here
4. **Anti-affinity ensures** Pod 7 is on a different node than Pods 1-6
5. **Cache hit**: Pod 7 has embeddings for media tenant 1 cached (50ms query time)
6. **Pod 7 warms up**: After 5 minutes, receives full traffic (cache fully populated)

Result: We get the cache locality benefits of tenant affinity without the blast radius of all pods on one node."

**INSTRUCTOR GUIDANCE:**
- Emphasize the tension between affinity (cache locality) and anti-affinity (fault tolerance)
- Use concrete numbers (41% latency improvement, 5-minute warm-up) to show impact
- Explain the warm-up period: this prevents the '3 AM scale-up latency spike' incident
- Connect to GCC scale: at 50 tenants, cache locality is the difference between 50ms and 85ms latency across millions of queries
- Preview Section 4: 'We'll write the Deployment manifest with affinity rules'

---

## SECTION 3: TECHNOLOGY STACK & ARCHITECTURE (3-5 minutes, 600-800 words)

**[10:30-12:00] Technology Stack Overview**

[SLIDE: Multi-Tenant Auto-Scaling Technology Stack showing:
- Kubernetes (orchestration, HPA, quotas)
- Prometheus (metrics collection, custom metrics)
- Prometheus Adapter (custom metrics API for HPA)
- Redis (cache, pod warm-up state)
- FastAPI (RAG service application)
- Python client libraries (kubernetes, prometheus_client)]

**NARRATION:**
"Let's map out the complete technology stack for multi-tenant auto-scaling. This isn't a single tool—it's an integrated system of 6 components working together.

**Component #1: Kubernetes (v1.27+)**

Kubernetes is the orchestration platform. We use:
- **Horizontal Pod Autoscaler (HPA)**: Scales deployment replicas based on metrics
- **Resource Quotas**: Enforces namespace-level resource caps
- **LimitRanges**: Enforces pod-level resource defaults and limits
- **Service with session affinity**: Routes queries to same pod for cache locality
- **Deployment with affinity rules**: Distributes pods across nodes

**Why this version**: Kubernetes 1.27 (May 2023 release) includes improved HPA behavior configuration (scale-up/scale-down stabilization windows) that prevents flapping. Earlier versions (1.24 and below) lack this fine-grained control.

**Component #2: Prometheus (v2.45+)**

Prometheus is our metrics collection system. We use it to:
- Scrape custom metrics from RAG service pods every 15 seconds
- Store time-series data (7-day retention in our setup)
- Provide PromQL queries for analysis (e.g., `rate(tenant_queue_depth[5m])`)
- Alert on threshold breaches (e.g., 'queue depth >50 for >2 minutes')

**Key metric we're exporting**: `tenant_queue_depth{tenant_id="media-1"}` - number of queued queries per tenant.

**Component #3: Prometheus Adapter (v0.11+)**

Prometheus Adapter translates Prometheus metrics into the Kubernetes Custom Metrics API format that HPA understands. Without this, HPA can't read our custom `tenant_queue_depth` metric—it only knows about CPU and memory (from Metrics Server).

The adapter runs as a Kubernetes Deployment and registers itself as a custom metrics API provider. HPA queries it like: `kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1/namespaces/default/pods/*/queue_depth_per_tenant` and gets back the current average value.

**Component #4: Redis (v7.0+)**

Redis serves two purposes in our stack:
1. **Cache for tenant embeddings**: Each pod caches embeddings for 5-10 tenants it's actively serving (reduces vector DB latency from 20ms to <1ms)
2. **Pod warm-up state tracking**: When a new pod starts, it sets a `warming_up` flag in Redis with 5-minute TTL, signaling to the load balancer to send reduced traffic

We use Redis Cluster mode for multi-tenant isolation: tenant embeddings are stored in separate keyspaces (`cache:media-1:*`, `cache:finance-1:*`).

**Component #5: FastAPI (Python 3.11+)**

FastAPI is our RAG service application framework. It exposes:
- **Query endpoint**: `POST /query` with tenant ID header
- **Metrics endpoint**: `GET /metrics` in Prometheus format, exposing `tenant_queue_depth`
- **Health endpoint**: `GET /health` for Kubernetes readiness/liveness probes

FastAPI handles request queuing: if a query arrives and the pod is overloaded, it's added to an in-memory queue (Python `asyncio.Queue`) until capacity frees up. The queue depth is what we export to Prometheus.

**Component #6: Python Client Libraries**

We use Python libraries to interact with Kubernetes and Prometheus:
- **`kubernetes` (v28.1.0)**: For reading pod metadata, namespace info (useful for debugging)
- **`prometheus_client` (v0.19.0)**: For exporting custom metrics to Prometheus
- **`redis-py` (v5.0.1)**: For cache and warm-up state management

**Architecture Flow (Request to Scale Decision)**

Let me trace a complete flow so you see how these components interact:

1. **T+0s**: Media tenant 1 sends 100 queries to RAG service (normal load is 10 queries)
2. **T+1s**: FastAPI receives queries, load balancer distributes across 10 pods (10 queries per pod)
3. **T+2s**: Each pod's query queue depth increases from 2 to 12 (10 new + 2 backlog)
4. **T+3s**: FastAPI exports metric: `tenant_queue_depth{tenant_id="media-1", pod="rag-service-abc123"} 12`
5. **T+15s**: Prometheus scrapes all 10 pods, collects 10 data points (all showing queue depth 11-13)
6. **T+30s**: HPA queries Prometheus Adapter: 'What's the current average queue depth per tenant?'
7. **T+31s**: Prometheus Adapter runs PromQL: `avg(tenant_queue_depth{tenant_id=~".*"}) by (tenant_id)` and returns: `{tenant_id="media-1"} 12.1`
8. **T+32s**: HPA calculates: `desiredReplicas = ceil(10 × (12.1 / 10)) = 13 pods`
9. **T+33s**: HPA updates Deployment: `spec.replicas: 13`
10. **T+35s**: Kubernetes scheduler provisions 3 new pods (13 - 10 = 3 additional)
11. **T+60s**: New pods pass readiness probe, start accepting traffic
12. **T+90s**: Queue depth drops to 8 per tenant (load distributed across 13 pods)

Total time from spike to resolution: **90 seconds**. This meets our 2-minute SLA.

**The Dependency Chain**

Here's what breaks if components are misconfigured:

- **No Prometheus Adapter**: HPA can't read custom metrics, falls back to CPU-only (noisy neighbor problem returns)
- **No Resource Quotas**: Tenants can monopolize cluster during scale-up (defeats purpose)
- **No Redis warm-up tracking**: New pods get full traffic immediately, cache misses cause latency spikes
- **No session affinity**: Every query is a cache miss (40% latency penalty)

All 6 components are mandatory for production-grade multi-tenant auto-scaling."

**INSTRUCTOR GUIDANCE:**
- Walk through the 90-second flow with timestamps—this makes the system tangible
- Emphasize the dependency chain: each component is necessary, none are optional
- Use version numbers (Kubernetes 1.27, Prometheus 2.45) so learners can verify compatibility
- Connect to Section 4: 'We'll configure each of these 6 components with working manifests and code'

---

**[12:00-13:30] System Architecture Diagram**

[SLIDE: Complete Multi-Tenant Auto-Scaling Architecture showing:
- Ingress (tenant query entry point)
- Service with session affinity
- Pods (rag-service) with resource requests/limits
- HPA monitoring custom metrics
- Prometheus scraping /metrics endpoints
- Prometheus Adapter exposing custom metrics API
- Resource Quotas per namespace
- Redis cluster for caching
- Flow arrows: Query → Load Balance → Pod → Cache Check → Vector DB (if cache miss) → Response]

**NARRATION:**
"Before we dive into code, let's visualize the complete architecture. I want you to see how all 6 components connect in a production GCC deployment.

**The Query Path (Left to Right):**

1. **Ingress**: Media tenant 1 query arrives at cluster ingress (Nginx or cloud load balancer) with header `X-Tenant-ID: media-1`
2. **Service**: Kubernetes Service with `sessionAffinity: ClientIP` routes query to Pod 7 (media-1's cached pod)
3. **Pod Resource Check**: Kubernetes checks if `tenant-media-1` namespace has quota for this query (CPU/memory available?)
4. **Pod Processing**: FastAPI application on Pod 7 checks Redis cache for media-1 embeddings (cache hit! <1ms)
5. **Query Execution**: Pod generates answer using cached embeddings, responds in 50ms total
6. **Metrics Export**: Pod increments `tenant_queue_depth` metric (if query had to wait) and exports to Prometheus on next scrape

**The Scaling Path (Top to Bottom):**

1. **Prometheus Scrape**: Every 15 seconds, Prometheus scrapes `/metrics` from all 10 pods
2. **Metric Aggregation**: Prometheus calculates average queue depth: `(12+11+13+...)/10 = 11.9`
3. **Custom Metrics API**: Prometheus Adapter exposes this metric to Kubernetes
4. **HPA Decision**: Every 60 seconds, HPA queries adapter, sees 11.9 > 10 (target), decides to scale up
5. **Deployment Update**: HPA sets `spec.replicas: 13` on Deployment
6. **Scheduler Action**: Kubernetes scheduler provisions 3 new pods on nodes with available capacity
7. **Anti-Affinity Check**: Scheduler ensures new pods land on different nodes (fault tolerance)
8. **Pod Startup**: New pods start, set 'warming up' flag in Redis, pre-load embeddings for top 5 tenants
9. **Load Balancer**: Service detects new pods, adds to rotation with 20% traffic (warm-up period)
10. **Metrics Update**: Prometheus scrapes new pods, HPA sees queue depth drop to 8, satisfied

**The Quota Enforcement Path (Dashed Lines):**

At every step where resources are allocated (pod scheduling, CPU usage, memory allocation), Kubernetes checks:
- **ResourceQuota**: Does `tenant-media-1` namespace have budget for this pod?
- **LimitRange**: Does this pod's spec comply with min/max limits?

If either check fails, pod scheduling is blocked with error: 'Quota exceeded' or 'Limit violation'. This prevents monopoly even during scale-up.

**Critical Integration Points:**

1. **FastAPI ↔ Prometheus**: Application must export metrics in Prometheus format on `/metrics` endpoint
2. **Prometheus ↔ Adapter**: Adapter queries Prometheus every 30 seconds, caches results
3. **Adapter ↔ HPA**: HPA queries adapter every 60 seconds for custom metrics
4. **HPA ↔ Deployment**: HPA updates Deployment spec, Kubernetes reconciles to desired state
5. **Pod ↔ Redis**: Pod reads cache and warm-up state, writes new embeddings after cache misses

Any broken link in this chain causes system degradation:
- FastAPI metrics broken → HPA sees no custom metrics, scales on CPU only (noisy neighbor returns)
- Adapter down → HPA falls back to CPU, custom metrics ignored
- Redis down → Every query is a cache miss, latency spikes to 85ms
- Anti-affinity misconfigured → All pods on one node, single point of failure

**The Feedback Loop:**

This is a closed-loop system:
- More queries → Higher queue depth → HPA scales up → More pods → Queries distributed → Lower queue depth → HPA scales down (after stabilization) → Fewer pods → Cost savings

The system self-regulates based on actual tenant load, not static provisioning. That's the power of auto-scaling."

**INSTRUCTOR GUIDANCE:**
- Use the diagram to show simultaneous paths: queries flowing left-to-right, metrics flowing bottom-to-top, quota checks enforcing throughout
- Emphasize the feedback loop: this is control theory applied to infrastructure
- Point out failure modes: 'What breaks if Redis is down? What breaks if Prometheus Adapter crashes?'
- Connect to Section 4: 'Now that you see the architecture, we'll configure each component'

---

## SECTION 4: TECHNICAL IMPLEMENTATION (15-18 minutes, 3,000-3,500 words WITH CODE)

**[13:30-15:30] Kubernetes HPA Configuration**

[SLIDE: HPA Manifest Structure showing:
- apiVersion, kind, metadata
- scaleTargetRef (which Deployment to scale)
- minReplicas, maxReplicas
- metrics (custom pod metrics)
- behavior (scale-up/scale-down policies)]

**NARRATION:**
"Now we're writing production code. This isn't pseudocode or conceptual examples—this is what runs in Indian GCC platforms managing 50+ tenants and ₹30 lakh monthly infrastructure.

Let's start with the Horizontal Pod Autoscaler manifest. This is the brain of our auto-scaling system."

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: rag-service-hpa
  namespace: default
  labels:
    app: rag-service
    component: autoscaler
spec:
  # Which Deployment does this HPA manage?
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: rag-service
  
  # Minimum replicas - always maintain baseline capacity for 50 tenants
  # Even at 3am with zero load, we need 3 pods to handle sudden spikes
  # Cost: ₹6,000/month baseline (3 pods × ₹2,000/pod)
  minReplicas: 3
  
  # Maximum replicas - budget ceiling set by CFO
  # 20 pods = ₹40,000/month max infrastructure cost
  # If we need >20 pods, it's time to optimize query efficiency or add nodes
  maxReplicas: 20
  
  # Metrics that drive scaling decisions
  metrics:
  # Primary metric: per-tenant queue depth (custom metric from Prometheus)
  - type: Pods
    pods:
      metric:
        # This metric name must match what Prometheus Adapter exposes
        # See prometheus-adapter ConfigMap later in this section
        name: queue_depth_per_tenant
      target:
        type: AverageValue
        # Scale up if average queue depth exceeds 10 queries per tenant
        # Why 10? Testing showed: <10 = <200ms latency, >10 = latency degrades
        averageValue: "10"
  
  # Secondary metric: CPU utilization (fallback if custom metrics fail)
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        # Scale up if CPU >70% across pods
        # This prevents complete saturation during custom metrics outage
        averageUtilization: 70
  
  # Scaling behavior - prevents flapping and runaway costs
  behavior:
    scaleUp:
      # Wait 60 seconds before scaling up (avoid reacting to brief spikes)
      # Example: Brief 3-second spike doesn't trigger scale-up
      stabilizationWindowSeconds: 60
      
      policies:
      # Policy 1: Add up to 4 pods per minute (prevents resource exhaustion)
      # If we need to go from 5 to 15 pods, takes 3 minutes (5→9→13→15)
      - type: Pods
        value: 4
        periodSeconds: 60
      
      # Policy 2: Increase by up to 100% per minute (doubles capacity quickly)
      # If we have 3 pods, can scale to 6 in first minute
      - type: Percent
        value: 100
        periodSeconds: 60
      
      # HPA uses the MORE aggressive policy (adds more pods faster)
      # This ensures we scale up quickly during genuine spikes
      selectPolicy: Max
    
    scaleDown:
      # Wait 5 minutes before scaling down (ensure load is truly gone)
      # Prevents the '3am scale-down-then-immediate-scale-up' flapping
      stabilizationWindowSeconds: 300
      
      policies:
      # Policy 1: Remove max 2 pods per 2 minutes (gradual scale-down)
      # Prevents sudden capacity loss that causes latency spikes
      - type: Pods
        value: 2
        periodSeconds: 120
      
      # Policy 2: Decrease by max 10% per 2 minutes (conservative)
      # If we have 20 pods, removes max 2 pods every 2 min (20→18→16→...)
      - type: Percent
        value: 10
        periodSeconds: 120
      
      # HPA uses the LESS aggressive policy (removes fewer pods)
      # This ensures we don't scale down too quickly and cause outages
      selectPolicy: Min
```

**NARRATION:**
"Let me explain the key decisions in this HPA configuration:

**Decision #1: minReplicas = 3**

Why not 1? Because Kubernetes pod startup time is 30-90 seconds. If we scale from 1 to 10 pods during a spike, the first 9 pods take 1-2 minutes to start. During that time, queries are queuing on the single pod, latency spikes to 15+ seconds.

With minReplicas = 3, we have baseline capacity. A spike triggers scale from 3 to 10 (7 new pods), but the initial 3 pods handle the load until reinforcements arrive. Cost is ₹6,000/month for 24/7 readiness—acceptable for 50-tenant platform.

**Decision #2: maxReplicas = 20**

This is a HARD budget constraint from the CFO. At ₹2,000 per pod-month, 20 pods = ₹40,000/month. If we hit this ceiling and still have latency problems, we have two choices:
1. Optimize query efficiency (reduce embedding size, faster models)
2. Tell CFO we need higher budget

Setting maxReplicas prevents 'runaway scaling' where HPA adds 50 pods and generates a ₹1 lakh surprise bill.

**Decision #3: Custom metric 'queue_depth_per_tenant'**

We could scale on CPU or memory, but those are lagging indicators. By the time CPU hits 80%, queries are already queuing for 10+ seconds. Queue depth is a LEADING indicator—it tells us 'load is incoming' before pods are saturated.

**Decision #4: Stabilization windows (60s up, 300s down)**

The 60-second scale-up window prevents reacting to brief anomalies. Example: A media tenant sends 100 queries in 5 seconds (fat-finger in UI), then stops. Without stabilization, HPA scales up, realizes load is gone, scales down—all within 2 minutes. That's flapping, and it causes latency spikes for OTHER tenants during the rapid scale changes.

The 300-second (5-minute) scale-down window is even more conservative. We'd rather run extra pods for 5 minutes and waste ₹5 than scale down prematurely and cause a latency spike that costs ₹50,000 in SLA penalties.

**Decision #5: Asymmetric policies (Max for scale-up, Min for scale-down)**

We scale up aggressively (100% increase or +4 pods, whichever is more) because the cost of under-provisioning (latency, SLA breaches) is high.

We scale down conservatively (10% decrease or -2 pods, whichever is less) because the cost of over-provisioning (₹2,000/pod-month) is lower than the cost of scale-down-induced outages.

This asymmetry is intentional—it's risk management translated into HPA policy."

**INSTRUCTOR GUIDANCE:**
- Walk through each parameter with reasoning: 'Why this value, not a different value?'
- Emphasize the economic constraints: maxReplicas is a CFO decision, not a technical one
- Explain stabilization windows with concrete examples (fat-finger scenario, 5-minute confidence period)
- Connect to earlier section: 'Remember the 2-minute scale-up target? The 60-second stabilization + 30-60 second pod startup = 90-120 seconds total'

---

**[15:30-17:30] Custom Metrics Exporter (FastAPI Application)**

[SLIDE: Prometheus Metrics Endpoint Flow showing:
- FastAPI app receives query
- Query added to asyncio.Queue
- Metrics updated (queue depth increment)
- Prometheus scrapes /metrics endpoint
- Metrics exported in Prometheus format]

**NARRATION:**
"The HPA needs custom metrics. But where do those metrics come from? From our FastAPI application—this is the code that exports `queue_depth_per_tenant` to Prometheus."

```python
# File: rag_service/metrics.py
"""
Prometheus metrics exporter for multi-tenant RAG service.

This module exports per-tenant queue depth metrics that drive HPA scaling decisions.
Each tenant gets their own Gauge metric to track queued queries.
"""

from prometheus_client import Gauge, Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Request, Response
from typing import Dict
import asyncio
import os

# Initialize FastAPI app
app = FastAPI(title="Multi-Tenant RAG Service")

# Prometheus metrics
# Gauge: Value that can go up and down (queue depth)
tenant_queue_depth = Gauge(
    'tenant_queue_depth',
    'Number of queued queries per tenant (drives HPA scaling)',
    ['tenant_id']  # Label by tenant ID for per-tenant visibility
)

# Counter: Value that only increases (total queries processed)
total_queries_processed = Counter(
    'total_queries_processed',
    'Total queries processed since service start',
    ['tenant_id', 'status']  # Labels: tenant ID, status (success/failure)
)

# Histogram: Latency distribution
query_latency_seconds = Histogram(
    'query_latency_seconds',
    'Query processing latency in seconds',
    ['tenant_id'],  # Label by tenant for per-tenant latency tracking
    buckets=[0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]  # Latency buckets (50ms to 5s)
)

# In-memory queue for each tenant (async queues for FastAPI)
tenant_queues: Dict[str, asyncio.Queue] = {}
MAX_QUEUE_SIZE = 100  # Per-tenant queue size limit (prevents memory exhaustion)

def get_or_create_tenant_queue(tenant_id: str) -> asyncio.Queue:
    """
    Get tenant's query queue, creating if doesn't exist.
    
    Why per-tenant queues? Isolation. If media tenant floods with 1000 queries,
    finance tenant queries don't get blocked. They have separate queues.
    """
    if tenant_id not in tenant_queues:
        tenant_queues[tenant_id] = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)
        # Initialize queue depth metric for this tenant
        tenant_queue_depth.labels(tenant_id=tenant_id).set(0)
    return tenant_queues[tenant_id]

@app.post("/query")
async def process_query(request: Request):
    """
    RAG query endpoint with per-tenant queuing.
    
    Flow:
    1. Extract tenant ID from request header
    2. Add query to tenant's queue (or return 429 if queue full)
    3. Update queue depth metric (Prometheus scrapes this)
    4. Process query async
    5. Decrement queue depth when done
    """
    # Extract tenant ID from header (required)
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return {"error": "Missing X-Tenant-ID header"}, 400
    
    # Get tenant's queue
    queue = get_or_create_tenant_queue(tenant_id)
    
    # Check if queue is full (backpressure mechanism)
    if queue.full():
        # Queue at capacity - return 429 Too Many Requests
        # This tells client to retry later (exponential backoff)
        # HPA will scale up in 60-120 seconds if sustained load
        return {
            "error": "Tenant query queue full (max 100). Retry in 30s",
            "tenant_id": tenant_id,
            "queue_size": queue.qsize()
        }, 429
    
    # Add query to queue (non-blocking)
    try:
        query_data = await request.json()
        await queue.put(query_data)
        
        # Update Prometheus metric (this is what HPA reads)
        current_depth = queue.qsize()
        tenant_queue_depth.labels(tenant_id=tenant_id).set(current_depth)
        
        # Process query asynchronously (doesn't block FastAPI response)
        # Background task handles actual RAG processing
        asyncio.create_task(_process_query_background(tenant_id, query_data, queue))
        
        return {
            "status": "queued",
            "tenant_id": tenant_id,
            "queue_position": current_depth,
            "estimated_wait_ms": current_depth * 200  # 200ms per query avg
        }
    
    except Exception as e:
        total_queries_processed.labels(tenant_id=tenant_id, status="error").inc()
        return {"error": str(e)}, 500

async def _process_query_background(tenant_id: str, query_data: dict, queue: asyncio.Queue):
    """
    Background task that processes queued queries.
    
    This is where actual RAG happens: embedding generation, vector search,
    LLM query, response generation. Details in M11-M12 (not focus here).
    
    Key: After processing, we DECREMENT queue depth metric so HPA knows load decreased.
    """
    import time
    start_time = time.time()
    
    try:
        # Simulate RAG processing (replace with actual RAG code)
        # In production: generate_embeddings() → vector_search() → llm_query()
        await asyncio.sleep(0.2)  # Simulated 200ms processing
        
        # Mark query as processed (remove from queue)
        await queue.get()
        queue.task_done()
        
        # Update metrics
        processing_time = time.time() - start_time
        query_latency_seconds.labels(tenant_id=tenant_id).observe(processing_time)
        total_queries_processed.labels(tenant_id=tenant_id, status="success").inc()
        
        # Decrement queue depth (HPA sees this and may scale down if sustained low load)
        current_depth = queue.qsize()
        tenant_queue_depth.labels(tenant_id=tenant_id).set(current_depth)
    
    except Exception as e:
        # Error handling
        await queue.get()  # Still remove from queue
        queue.task_done()
        total_queries_processed.labels(tenant_id=tenant_id, status="error").inc()
        current_depth = queue.qsize()
        tenant_queue_depth.labels(tenant_id=tenant_id).set(current_depth)

@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    HPA scaling flow:
    1. Prometheus scrapes this endpoint every 15 seconds
    2. Prometheus stores: tenant_queue_depth{tenant_id="media-1"} 12
    3. Prometheus Adapter averages across all tenants
    4. HPA queries adapter, gets average=11.9, decides to scale
    
    Format: Prometheus exposition format (text-based)
    Example output:
    # HELP tenant_queue_depth Number of queued queries per tenant
    # TYPE tenant_queue_depth gauge
    tenant_queue_depth{tenant_id="media-1"} 12.0
    tenant_queue_depth{tenant_id="finance-1"} 3.0
    ...
    """
    # Generate Prometheus exposition format
    metrics_data = generate_latest()
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
async def health_check():
    """
    Kubernetes readiness/liveness probe.
    
    HPA only routes traffic to 'ready' pods. This endpoint tells Kubernetes:
    'Pod is ready to accept traffic' (returns 200 OK).
    
    During warm-up period (first 5 min), we still return 200 here, but we
    set a Redis flag that load balancer checks to reduce traffic.
    """
    return {"status": "healthy", "queues": len(tenant_queues)}

# Application startup: Pre-load embeddings (warm-up)
@app.on_event("startup")
async def startup_event():
    """
    Pod startup warm-up period.
    
    When a new pod starts (HPA scaled up), we don't want immediate full traffic.
    Cache is cold—every query would be a cache miss (85ms latency vs 50ms).
    
    Solution: Pre-load embeddings for top 5 active tenants (warm the cache).
    Mark pod as 'warming up' in Redis for 5 minutes (load balancer sends 20% traffic).
    """
    import redis
    from rag_service.embedding_cache import load_tenant_embeddings, get_top_active_tenants
    
    # Connect to Redis
    redis_client = redis.Redis(host='redis-service', port=6379, decode_responses=True)
    
    # Mark pod as warming up (TTL 300 seconds = 5 minutes)
    pod_ip = os.getenv('POD_IP', 'unknown')
    redis_client.setex(f"pod:{pod_ip}:warming_up", 300, "true")
    
    # Pre-load embeddings for top 5 active tenants (based on last 1-hour query volume)
    top_tenants = get_top_active_tenants(limit=5)
    for tenant_id in top_tenants:
        print(f"Pre-loading embeddings for tenant: {tenant_id}")
        await load_tenant_embeddings(tenant_id)  # Async embedding load
    
    print(f"Pod {pod_ip} warm-up complete. Ready for full traffic in 5 minutes.")
    
    # After 5 minutes, remove warming-up flag (pod is now 'hot')
    await asyncio.sleep(300)
    redis_client.delete(f"pod:{pod_ip}:warming_up")
    print(f"Pod {pod_ip} now accepting full traffic (warm-up period ended).")
```

**NARRATION:**
"Let's walk through the key parts of this code:

**Line 24-28: tenant_queue_depth Gauge**

This is the metric HPA reads. It's a Prometheus Gauge (value can go up/down) labeled by `tenant_id`. When HPA queries 'average queue depth per tenant,' Prometheus Adapter calculates:

```
avg(tenant_queue_depth{tenant_id=~".*"})
```

This returns a single number (e.g., 11.9) that HPA uses in the scaling formula.

**Line 49-54: Per-Tenant Queues**

Why separate queues? Isolation. If media tenant floods with 1000 queries, they fill THEIR queue (max 100), and further queries get 429 Too Many Requests. But finance tenant queries go to a separate queue—unaffected.

Without per-tenant queues, 1000 media queries would block finance queries in a shared global queue. That's the noisy neighbor problem at the application level.

**Line 78-82: Queue Full → 429 Response**

When a tenant's queue hits 100 queries (configurable), we return HTTP 429. This is backpressure—we're telling the client 'slow down, we're processing as fast as we can.'

Critically, this gives HPA time to scale up. HPA sees sustained high queue depth (100 queries for 60+ seconds), triggers scale-up. New pods come online in 2 minutes. During those 2 minutes, the 429 responses tell clients to retry with exponential backoff.

**Line 92: asyncio.create_task()**

We don't block the HTTP response waiting for RAG processing. We queue the query, update the metric, and return immediately with 'queued' status. The actual processing happens asynchronously in the background.

Why? If we block, each query takes 200ms. That means each FastAPI worker can only handle 5 queries/second. With async processing, we can accept 100 queries/second and queue them. HPA sees the queue depth and scales accordingly.

**Line 138-143: _process_query_background() decrements queue depth**

After processing, we call `queue.get()` (removes query from queue) and update the metric: `tenant_queue_depth.labels(tenant_id=tenant_id).set(current_depth)`.

This is critical for scale-down. If we process 100 queries and DON'T decrement the metric, HPA thinks load is still high and never scales down. We'd stay at 20 pods forever, wasting ₹20,000/month.

**Line 168-176: /metrics endpoint**

Prometheus scrapes this every 15 seconds. The output looks like:

```
# HELP tenant_queue_depth Number of queued queries per tenant
# TYPE tenant_queue_depth gauge
tenant_queue_depth{tenant_id="media-1"} 12.0
tenant_queue_depth{tenant_id="finance-1"} 3.0
tenant_queue_depth{tenant_id="retail-1"} 1.0
```

Prometheus stores this time-series data. When HPA queries Prometheus Adapter, it runs a PromQL query to calculate the average.

**Line 189-205: Warm-up period**

When a pod starts, we:
1. Set a Redis flag: `pod:{pod_ip}:warming_up = true` with 5-minute TTL
2. Pre-load embeddings for top 5 active tenants (cache warming)
3. After 5 minutes, delete the Redis flag (pod is now 'hot')

Our load balancer (configured separately) checks this Redis flag. If present, it sends only 20% of normal traffic to this pod. After 5 minutes, the pod gets full traffic.

This prevents the 'cold start latency spike' where new pods get immediate full load with empty caches."

**INSTRUCTOR GUIDANCE:**
- Walk through the code with line-by-line explanations (don't assume learners understand async Python)
- Emphasize the metrics flow: update metric → Prometheus scrapes → Adapter exposes → HPA decides
- Explain the 429 backpressure mechanism: this isn't failure, it's intentional load shedding
- Connect to HPA: 'This code exports the metric HPA reads. If this code breaks, HPA falls back to CPU-only scaling'

---

**[17:30-19:00] Prometheus Adapter Configuration**

[SLIDE: Prometheus Adapter Architecture showing:
- Prometheus with time-series data
- Adapter with custom rules
- Kubernetes Custom Metrics API
- HPA querying custom metrics]

**NARRATION:**
"We're exporting metrics from FastAPI. Prometheus is scraping them. But HPA can't read Prometheus directly—it needs the Kubernetes Custom Metrics API. That's where Prometheus Adapter comes in."

```yaml
# File: prometheus-adapter-config.yaml
# ConfigMap for Prometheus Adapter
# This translates Prometheus metrics into Kubernetes Custom Metrics API format

apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-adapter-config
  namespace: monitoring
data:
  config.yaml: |
    # Rules define how to translate Prometheus metrics to Kubernetes metrics
    rules:
    # Rule 1: Per-tenant queue depth (primary HPA metric)
    - seriesQuery: 'tenant_queue_depth{namespace!="",pod!=""}'
      # PromQL query to fetch metric data from Prometheus
      # Matches: tenant_queue_depth{tenant_id="media-1", namespace="default", pod="rag-service-abc123"}
      
      resources:
        # Map Prometheus labels to Kubernetes resource identifiers
        # HPA needs to know: which namespace, which pods
        overrides:
          namespace: {resource: "namespace"}
          pod: {resource: "pod"}
      
      name:
        # Metric name exposed to Kubernetes (what HPA queries)
        # Format: queue_depth_per_tenant (matches HPA spec)
        matches: "^tenant_queue_depth$"
        as: "queue_depth_per_tenant"
      
      metricsQuery: |
        # PromQL query to calculate the metric value HPA sees
        # This is the CRITICAL part - how we aggregate per-tenant queue depth
        
        # Step 1: Get queue depth per pod per tenant
        # Example: tenant_queue_depth{tenant_id="media-1", pod="rag-service-abc123"} 12
        
        # Step 2: Sum across all pods for each tenant
        # sum(tenant_queue_depth{<<.LabelMatchers>>}) by (tenant_id)
        # Result: {tenant_id="media-1"} 120 (summed across 10 pods)
        
        # Step 3: Calculate average queue depth per tenant
        # 120 queries / 10 pods = 12 queries per tenant
        # But HPA needs a single number, not per-tenant breakdown
        
        # Step 4: Average across all tenants
        # avg(sum(tenant_queue_depth{<<.LabelMatchers>>}) by (tenant_id))
        # Result: 11.9 (average queue depth across all 50 tenants)
        
        # Final PromQL query (what adapter sends to Prometheus)
        avg(sum(tenant_queue_depth{<<.LabelMatchers>>}) by (tenant_id))
      
      # This rule exposes metric as 'pods/queue_depth_per_tenant'
      # HPA queries: kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1/namespaces/default/pods/*/queue_depth_per_tenant
    
    # Rule 2: Query latency (for monitoring, not HPA)
    - seriesQuery: 'query_latency_seconds{namespace!="",pod!=""}'
      resources:
        overrides:
          namespace: {resource: "namespace"}
          pod: {resource: "pod"}
      name:
        matches: "^query_latency_seconds$"
        as: "query_latency_p50"
      metricsQuery: |
        # Calculate 50th percentile (median) latency per tenant
        # This isn't used for HPA, but useful for tenant SLA monitoring
        histogram_quantile(0.50, sum(rate(query_latency_seconds_bucket{<<.LabelMatchers>>}[5m])) by (le, tenant_id))
---
# Deployment for Prometheus Adapter
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus-adapter
  namespace: monitoring
spec:
  replicas: 2  # High availability (if one pod crashes, other handles HPA queries)
  selector:
    matchLabels:
      app: prometheus-adapter
  template:
    metadata:
      labels:
        app: prometheus-adapter
    spec:
      containers:
      - name: prometheus-adapter
        image: registry.k8s.io/prometheus-adapter/prometheus-adapter:v0.11.0
        args:
        # Point adapter to Prometheus server
        - --prometheus-url=http://prometheus-service.monitoring.svc:9090
        # Load rules from ConfigMap
        - --config=/etc/adapter/config.yaml
        # Secure metrics endpoint (optional, for adapter's own metrics)
        - --metrics-relist-interval=30s
        # How often to refresh custom metrics from Prometheus
        - --cert-dir=/tmp/cert
        - --secure-port=6443
        volumeMounts:
        - name: config
          mountPath: /etc/adapter
        - name: temp
          mountPath: /tmp
        ports:
        - containerPort: 6443
          name: https
      volumes:
      - name: config
        configMap:
          name: prometheus-adapter-config
      - name: temp
        emptyDir: {}
---
# Service for Prometheus Adapter
apiVersion: v1
kind: Service
metadata:
  name: prometheus-adapter
  namespace: monitoring
spec:
  ports:
  - port: 443
    targetPort: 6443
  selector:
    app: prometheus-adapter
---
# APIService registration (makes adapter available to Kubernetes API)
apiVersion: apiregistration.k8s.io/v1
kind: APIService
metadata:
  name: v1beta1.custom.metrics.k8s.io
spec:
  service:
    name: prometheus-adapter
    namespace: monitoring
  group: custom.metrics.k8s.io
  version: v1beta1
  insecureSkipTLSVerify: true
  groupPriorityMinimum: 100
  versionPriority: 100
```

**NARRATION:**
"Let's break down the Prometheus Adapter configuration:

**Line 14-18: seriesQuery**

This is the Prometheus query that finds our metric. `tenant_queue_depth{namespace!="",pod!=""}` means: 'Find all `tenant_queue_depth` metrics that have namespace and pod labels.'

Why filter on namespace and pod? Because HPA needs to know: 'What's the queue depth for pods in the `default` namespace?' Without these labels, we can't scope the metric to specific resources.

**Line 27-29: Name mapping**

We're renaming `tenant_queue_depth` (Prometheus metric name) to `queue_depth_per_tenant` (Kubernetes custom metric name). This is what HPA queries.

Why rename? Kubernetes custom metrics have naming conventions: `resource_type/metric_name`. By using `queue_depth_per_tenant`, we're signaling this is a pod-level metric (as opposed to node-level or cluster-level).

**Line 31-50: metricsQuery (The Critical PromQL)**

This is where the magic happens. HPA doesn't want per-tenant queue depth—it wants a SINGLE NUMBER representing overall system load. We calculate this in 4 steps:

**Step 1**: Get raw metric values per pod per tenant
```
tenant_queue_depth{tenant_id="media-1", pod="rag-service-abc123"} 12
tenant_queue_depth{tenant_id="media-1", pod="rag-service-def456"} 11
...
```

**Step 2**: Sum across all pods for each tenant
```
sum(tenant_queue_depth) by (tenant_id)
Result:
{tenant_id="media-1"} 120  (10 pods × avg 12)
{tenant_id="finance-1"} 30  (10 pods × avg 3)
...
```

**Step 3**: Average across all tenants
```
avg(sum(tenant_queue_depth) by (tenant_id))
Result: 11.9
```

This single number (11.9) is what HPA sees. If it's above the target (10), HPA scales up.

**Why this formula?** We want to scale when TENANTS are experiencing load, not when PODS are busy. If 10 pods are processing 120 queries from 1 tenant, that's a tenant-specific spike. If 10 pods are processing 600 queries from 50 tenants, that's genuine platform load.

The `avg(sum(...) by (tenant_id))` formula captures 'average load per tenant,' which is what we care about for multi-tenant platforms.

**Line 78-83: Adapter deployment (replicas: 2)**

Why 2 replicas? Redundancy. HPA queries the adapter every 60 seconds. If the adapter crashes, HPA falls back to CPU-only scaling (noisy neighbor problem returns). With 2 replicas, one can crash and HPA keeps working.

**Line 98-108: APIService registration**

This tells Kubernetes: 'Hey, there's a new API available at `custom.metrics.k8s.io/v1beta1`. Route queries there to the `prometheus-adapter` service.'

After this is deployed, you can query custom metrics via:

```bash
kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1/namespaces/default/pods/*/queue_depth_per_tenant
```

Output:
```json
{
  "kind": "MetricValueList",
  "apiVersion": "custom.metrics.k8s.io/v1beta1",
  "metadata": {},
  "items": [
    {
      "describedObject": {
        "kind": "Pod",
        "namespace": "default",
        "name": "rag-service-abc123"
      },
      "metricName": "queue_depth_per_tenant",
      "timestamp": "2025-11-18T10:30:00Z",
      "value": "11900m"  # 11.9 (millis format)
    }
  ]
}
```

HPA reads this value and plugs it into the scaling formula."

**INSTRUCTOR GUIDANCE:**
- Emphasize the PromQL formula: this is THE critical piece that makes multi-tenant auto-scaling work
- Show the API query command: learners should test this themselves to verify adapter is working
- Explain the replica count: 2 for HA, not performance (adapter is lightweight)
- Connect to HPA: 'This adapter is the bridge between Prometheus (metrics) and HPA (scaling decisions)'

---

**[19:00-21:00] Resource Quotas and LimitRanges**

[SLIDE: Resource Quota Enforcement Flow showing:
- Tenant requests pod scheduling
- Kubernetes checks ResourceQuota (namespace-level)
- Kubernetes checks LimitRange (pod-level)
- If quotas available, pod scheduled
- If exceeded, pod blocked with error]

**NARRATION:**
"We have auto-scaling, but without resource quotas, one tenant can still monopolize the cluster. Let's fix that."

```yaml
# File: resource-quotas.yaml
# Per-tenant resource quotas (prevents monopoly)

# Gold Tier Tenant Quota (Example: tenant-media-1)
apiVersion: v1
kind: ResourceQuota
metadata:
  name: gold-tier-quota
  namespace: tenant-media-1
spec:
  hard:
    # CPU quotas (in cores)
    # 'requests.cpu' = guaranteed CPU (scheduler uses this for placement)
    # 'limits.cpu' = maximum CPU burst (cgroup hard limit)
    # Gold tier gets 30% of cluster (40 cores × 0.30 = 12 cores)
    requests.cpu: "8"     # Guaranteed 8 cores for this tenant
    limits.cpu: "12"      # Can burst up to 12 cores if cluster has spare capacity
    
    # Memory quotas (in GB)
    # Gold tier gets 30% of cluster memory (80GB × 0.30 = 24GB)
    requests.memory: "16Gi"  # Guaranteed 16GB
    limits.memory: "24Gi"    # Can burst up to 24GB
    
    # Pod count limit (prevents 'pod spam')
    # Gold tier can schedule max 10 pods across all Deployments in this namespace
    # Why cap pods? A tenant could try to schedule 100 tiny pods (resource exhaustion)
    pods: "10"
    
    # Persistent volume storage (if tenant stores embeddings on disk)
    # Gold tier gets 100GB storage quota
    persistentvolumeclaims: "5"  # Max 5 PVCs
    requests.storage: "100Gi"    # Max 100GB total storage
    
    # Service count (LoadBalancer/NodePort costs money)
    # Gold tier can create max 3 services (prevents cloud cost explosion)
    services.loadbalancers: "3"

---
# Silver Tier Tenant Quota (Example: tenant-finance-1)
apiVersion: v1
kind: ResourceQuota
metadata:
  name: silver-tier-quota
  namespace: tenant-finance-1
spec:
  hard:
    # Silver tier gets 50% of resources but shared across 20 tenants
    # Per tenant: (40 cores × 0.50) / 20 tenants = 1 core per tenant
    requests.cpu: "1"
    limits.cpu: "2"        # Can burst 2× during low contention
    requests.memory: "2Gi"
    limits.memory: "4Gi"
    pods: "3"              # Fewer pods than Gold
    persistentvolumeclaims: "2"
    requests.storage: "20Gi"  # Less storage than Gold
    services.loadbalancers: "1"

---
# Bronze Tier Tenant Quota (Example: tenant-retail-1)
apiVersion: v1
kind: ResourceQuota
metadata:
  name: bronze-tier-quota
  namespace: tenant-retail-1
spec:
  hard:
    # Bronze tier gets 20% of resources shared across 20 tenants
    # Per tenant: (40 cores × 0.20) / 20 tenants = 0.4 cores per tenant
    requests.cpu: "400m"   # 400 millicores (0.4 cores)
    limits.cpu: "800m"     # Can burst to 0.8 cores
    requests.memory: "800Mi"
    limits.memory: "1600Mi"  # 1.6GB max
    pods: "2"              # Minimal pod count
    persistentvolumeclaims: "1"
    requests.storage: "10Gi"
    services.loadbalancers: "0"  # Bronze doesn't get LoadBalancer (cost saving)

---
# LimitRange (Pod-level defaults and caps)
# Applied to ALL pods in a namespace
apiVersion: v1
kind: LimitRange
metadata:
  name: tenant-pod-limits
  namespace: tenant-media-1  # Apply to Gold tier tenant
spec:
  limits:
  # Container-level limits (most specific)
  - type: Container
    # Maximum resources a single container can request
    # Prevents: A developer deploys a pod with 'requests.cpu: 100' (typo)
    max:
      cpu: "4"        # No container can request >4 cores
      memory: "8Gi"   # No container can request >8GB
    
    # Minimum resources (enforce baseline)
    # Prevents: A developer deploys a pod with no resource spec (unbounded)
    min:
      cpu: "100m"     # Every container must request ≥100 millicores
      memory: "128Mi" # Every container must request ≥128MB
    
    # Default limits (if container spec omits limits)
    # When developer writes: 'containers: [{image: rag-service}]' with no resources
    # Kubernetes applies these defaults automatically
    default:
      cpu: "500m"     # Default CPU limit
      memory: "512Mi" # Default memory limit
    
    # Default requests (if container spec omits requests)
    # Scheduler uses requests for placement decisions
    defaultRequest:
      cpu: "250m"     # Default CPU request (scheduler assumes this)
      memory: "256Mi" # Default memory request
  
  # Pod-level limits (aggregate across all containers in pod)
  - type: Pod
    # Maximum resources a single pod can request (sum of all containers)
    # Prevents: A pod with 5 containers each requesting 2 cores (10 cores total)
    max:
      cpu: "8"        # No pod can have >8 cores total
      memory: "16Gi"  # No pod can have >16GB total
```

**NARRATION:**
"Let's understand how these quotas prevent the 'tenant monopoly' problem:

**Scenario: Media tenant tries to monopolize cluster**

1. **T+0**: HPA scales media tenant from 3 pods to 10 pods (traffic spike)
2. **T+30s**: Kubernetes scheduler tries to place 7 new pods
3. **T+31s**: Scheduler checks `tenant-media-1` namespace ResourceQuota:
   - Current usage: 3 pods × 500m CPU = 1.5 cores, 3 pods × 512Mi memory = 1.5GB
   - Requested: 7 pods × 500m CPU = 3.5 cores, 7 pods × 512Mi memory = 3.5GB
   - Total: 5 cores, 5GB (within quota: 8 cores, 16GB allowed)
   - **Result**: Quota check passes ✓
4. **T+32s**: Pods scheduled and started
5. **T+2min**: HPA tries to scale to 15 pods (spike continues)
6. **T+2min 1s**: Scheduler checks quota again:
   - Current: 10 pods × 500m = 5 cores
   - Requested: 5 more pods × 500m = 2.5 cores
   - Total: 7.5 cores (within quota: 8 cores allowed)
   - **Result**: Quota check passes ✓
7. **T+3min**: HPA tries to scale to 20 pods (spike peak)
8. **T+3min 1s**: Scheduler checks quota:
   - Current: 15 pods × 500m = 7.5 cores
   - Requested: 5 more pods × 500m = 2.5 cores
   - Total: 10 cores (EXCEEDS quota: 8 cores allowed)
   - **Result**: Quota check FAILS ✗
9. **T+3min 2s**: Kubernetes events:
   ```
   Warning  FailedScheduling  pod/rag-service-xyz789
   0/20 nodes are available: 5 Insufficient cpu, 15 node(s) exceeded resource quota.
   ```

**Outcome**: Media tenant is capped at 15 pods (7.5 cores). Even though HPA wants 20 pods, the ResourceQuota enforces the ceiling. Other tenants' quotas are unaffected—they still have their guaranteed 2 cores (silver) or 0.4 cores (bronze).

**The LimitRange Safety Net**

But what if a developer deploys a pod WITHOUT specifying resources?

```yaml
# Dangerous pod spec (no resources defined)
apiVersion: v1
kind: Pod
metadata:
  name: dangerous-pod
spec:
  containers:
  - name: app
    image: rag-service:latest
```

Without LimitRange, Kubernetes assigns NO resource requests/limits. The pod can consume unlimited CPU/memory until it crashes the node. This is the 'unbounded pod' problem.

With LimitRange, Kubernetes applies defaults:

```yaml
# What Kubernetes actually schedules (after LimitRange applied)
apiVersion: v1
kind: Pod
metadata:
  name: dangerous-pod
spec:
  containers:
  - name: app
    image: rag-service:latest
    resources:
      requests:
        cpu: 250m      # Defaulted by LimitRange
        memory: 256Mi  # Defaulted by LimitRange
      limits:
        cpu: 500m      # Defaulted by LimitRange
        memory: 512Mi  # Defaulted by LimitRange
```

Now the pod has sensible defaults. It can't crash the node. And the ResourceQuota can track its usage (requests.cpu += 250m).

**The Over-Subscription Strategy**

Notice we allocated:
- Gold: 30% (8 cores guaranteed, 12 burst)
- Silver: 50% across 20 tenants (20 cores guaranteed)
- Bronze: 20% across 20 tenants (8 cores guaranteed)
**Total: 36 cores guaranteed out of 40 cores cluster capacity**

Why not 40 cores? Over-subscription headroom. Not all tenants max out simultaneously. We provision 90% guaranteed capacity, leaving 10% for:
- Kubernetes system pods (kubelet, kube-proxy)
- Burst capacity (when tenants hit their 'limits' above 'requests')
- New tenant onboarding without re-balancing quotas

This is multi-tenant economics: shared infrastructure with statistical multiplexing."

**INSTRUCTOR GUIDANCE:**
- Walk through the quota violation scenario with timestamps—make it concrete
- Explain the difference between requests (guaranteed) and limits (burst): requests = what scheduler promises, limits = what cgroup enforces
- Show the LimitRange safety net: this prevents 'unbounded pod' incidents
- Emphasize over-subscription: this is why multi-tenant is cost-effective (not all tenants max out at once)

---

**[21:00-23:00] Deployment with Affinity Rules**

[SLIDE: Pod Affinity Visualization showing:
- Node A with 2 rag-service pods (anti-affinity violation)
- Node B with 1 rag-service pod
- Node C with 1 rag-service pod
- Scheduler blocks pod on Node A (anti-affinity enforced)]

**NARRATION:**
"Final piece: Deployment configuration with tenant-aware affinity rules."

```yaml
# File: rag-service-deployment.yaml
# Multi-tenant RAG service deployment with auto-scaling support

apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-service
  namespace: default
  labels:
    app: rag-service
    tier: backend
spec:
  # Don't set replicas here - HPA manages this
  # If you set replicas: 5, HPA will overwrite it
  # replicas: 5  # WRONG - omit this when using HPA
  
  # Pod update strategy (during scale-up or rolling update)
  strategy:
    type: RollingUpdate
    rollingUpdate:
      # During scale-up, add at most 4 pods at a time (prevents thundering herd)
      # If HPA wants to scale from 5 to 15 pods, adds 4→4→2 (gradual)
      maxSurge: 4
      
      # During scale-down or update, remove at most 2 pods at a time
      # Prevents sudden capacity loss that causes latency spikes
      maxUnavailable: 2
  
  selector:
    matchLabels:
      app: rag-service
  
  template:
    metadata:
      labels:
        app: rag-service
      annotations:
        # Prometheus scrape configuration (tells Prometheus to scrape this pod)
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    
    spec:
      # Affinity rules (WHERE should pods be scheduled?)
      affinity:
        # Pod anti-affinity: Spread pods across nodes (fault tolerance)
        podAntiAffinity:
          # 'required' = HARD constraint (Kubernetes won't schedule if violated)
          # Use 'preferred' for soft constraints (scheduler tries but not mandatory)
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - rag-service
            # Topology key: What defines 'different location'?
            # kubernetes.io/hostname = different physical nodes
            # topology.kubernetes.io/zone = different availability zones
            topologyKey: kubernetes.io/hostname
        
        # Node affinity: Prefer nodes with specific labels (optional)
        # Example: Prefer nodes in availability zone 'us-west-2a' for Gold tenants
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            preference:
              matchExpressions:
              - key: topology.kubernetes.io/zone
                operator: In
                values:
                - us-west-2a
                - us-west-2b  # Distribute across 2 zones minimum
      
      # Topology spread constraints (Advanced: distribute across zones)
      topologySpreadConstraints:
      - maxSkew: 1  # Max difference between zone with most/least pods
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule  # Block scheduling if can't satisfy
        labelSelector:
          matchLabels:
            app: rag-service
      
      containers:
      - name: rag-service
        image: gcr.io/my-gcc-project/rag-service:v1.2.3
        
        # Resource requests and limits (critical for HPA and quotas)
        resources:
          # Requests: Guaranteed resources (scheduler uses this for placement)
          # HPA calculates 'desired replicas' based on requests
          requests:
            cpu: "250m"     # 0.25 cores guaranteed
            memory: "256Mi" # 256MB guaranteed
          
          # Limits: Maximum burst capacity (cgroup hard limit)
          # If pod exceeds memory limit, it's OOM-killed
          # If pod exceeds CPU limit, it's throttled (not killed)
          limits:
            cpu: "500m"     # Can burst to 0.5 cores
            memory: "512Mi" # Can burst to 512MB
        
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP
        
        # Environment variables (configuration injection)
        env:
        - name: POD_IP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP  # Used for Redis warm-up flag
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: REDIS_HOST
          value: "redis-service.default.svc.cluster.local"
        - name: REDIS_PORT
          value: "6379"
        - name: PROMETHEUS_PORT
          value: "8000"  # Port where /metrics is served
        
        # Liveness probe (is pod alive? If not, restart it)
        # HPA doesn't route traffic to pods failing liveness probe
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30  # Wait 30s after pod starts before probing
          periodSeconds: 10        # Check every 10 seconds
          timeoutSeconds: 5        # Probe times out after 5s
          failureThreshold: 3      # Restart pod after 3 consecutive failures
        
        # Readiness probe (is pod ready for traffic?)
        # HPA only routes traffic to pods passing readiness probe
        # During warm-up, pod passes readiness but Redis flag reduces traffic
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10  # Check readiness 10s after pod starts
          periodSeconds: 5         # Check every 5 seconds (more frequent than liveness)
          timeoutSeconds: 3
          successThreshold: 1      # Pod is ready after 1 successful probe
          failureThreshold: 2      # Pod is NOT ready after 2 failures
        
        # Startup probe (for slow-starting apps)
        # Prevents liveness probe from killing pod during long startup
        # Not needed for FastAPI (starts in <10s), but useful for Java apps
        startupProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 12  # Allow up to 60s startup time (5s × 12 = 60s)
      
      # Graceful shutdown (for scale-down)
      terminationGracePeriodSeconds: 30  # Wait 30s before sending SIGKILL
      # During these 30s:
      # 1. Pod removed from Service endpoints (no new traffic)
      # 2. Existing requests complete (connection draining)
      # 3. Application receives SIGTERM, shuts down gracefully
      # 4. After 30s, Kubernetes sends SIGKILL (force kill)
```

**NARRATION:**
"Let's walk through the key affinity and anti-affinity rules:

**Line 56-67: podAntiAffinity (Fault Tolerance)**

This rule says: 'When scheduling a new `rag-service` pod, Kubernetes MUST place it on a node that doesn't already have another `rag-service` pod.'

Why? Blast radius containment. If Node A crashes and it has 10 of our 15 pods, we lose 67% of capacity. With anti-affinity, those 15 pods are spread across 15 nodes (assuming we have ≥15 nodes). Lose 1 node = lose 6.7% capacity.

**The Scheduling Constraint**

But anti-affinity creates a problem: If we have 12 nodes and HPA wants to scale to 15 pods, Kubernetes can't schedule the 13th, 14th, and 15th pods. They stay 'Pending' with event:

```
0/12 nodes are available: 12 node(s) didn't match pod anti-affinity rules.
```

Solution: Use Cluster Autoscaler or Karpenter to auto-scale nodes when pods are pending. For example:
- HPA wants 15 pods
- Only 12 nodes available (pods 1-12 scheduled)
- Pods 13-15 pending due to anti-affinity
- Cluster Autoscaler sees pending pods, adds 3 nodes
- Pods 13-15 scheduled on new nodes

This is why we set `maxReplicas: 20` conservatively. If we set maxReplicas: 50 and only have 20 nodes, we'd need to add 30 nodes, which takes 5-10 minutes (unacceptable during spike).

**Line 70-80: nodeAffinity (Zone Distribution)**

This is a 'preferred' rule (soft constraint). We PREFER scheduling pods in zones `us-west-2a` and `us-west-2b`, but if those zones are full, Kubernetes can schedule in other zones.

Why prefer specific zones? Cost. Inter-zone traffic costs ₹0.01/GB. Keeping pods in 2 nearby zones minimizes data transfer costs when pods communicate with Redis or vector database.

**Line 83-89: topologySpreadConstraints (Advanced)**

This rule says: 'Distribute pods across availability zones with maximum skew of 1.'

Example:
- We have 3 zones: A, B, C
- We have 10 pods
- Valid distributions: 4-3-3, 4-4-2, 3-3-4 (skew ≤1)
- Invalid distributions: 6-2-2, 5-5-0 (skew >1)

This prevents the 'all pods in one zone' scenario. If zone A fails (rare but happens), we don't lose all 10 pods. We lose at most 4.

**Line 98-110: resources (requests and limits)**

These values are CRITICAL for HPA. HPA uses `requests.cpu` and `requests.memory` to calculate how many pods fit on a node. If we set `requests.cpu: 4` (4 cores per pod), a 16-core node fits only 4 pods. If we set `requests.cpu: 250m` (0.25 cores per pod), the same node fits 64 pods.

We chose 250m CPU / 256Mi memory based on testing:
- RAG query processing uses ~200m CPU sustained, spikes to 400m during embedding generation
- Memory footprint: 128Mi base + 100Mi per cached tenant embeddings (we cache 1-2 tenants per pod)
- We set requests slightly below average (250m) and limits at peak (500m), allowing bursting

**Line 142-153: readinessProbe (Traffic Routing)**

HPA routes traffic ONLY to pods passing readiness probe. During the 5-minute warm-up period, pods pass readiness (they're healthy), but our application checks the Redis `warming_up` flag and sends 80% of traffic to 'hot' pods, 20% to 'warming' pods.

After 5 minutes, the Redis flag expires, and the pod gets 100% traffic.

**Line 171: terminationGracePeriodSeconds (Graceful Scale-Down)**

When HPA scales down (e.g., 15 pods → 10 pods), Kubernetes:
1. Removes 5 pods from Service endpoints (no NEW traffic sent)
2. Waits 30 seconds (existing requests complete)
3. Sends SIGTERM to pod (application shuts down gracefully)
4. After 30 seconds, sends SIGKILL (force kill)

Our FastAPI application handles SIGTERM:

```python
import signal

def handle_sigterm(signum, frame):
    print('SIGTERM received, draining connections...')
    # Stop accepting new requests
    app.shutdown()
    # Wait for in-flight requests to complete
    asyncio.run(wait_for_in_flight_requests())
    # Exit gracefully
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_sigterm)
```

This prevents the 'query aborted during scale-down' problem."

**INSTRUCTOR GUIDANCE:**
- Emphasize the anti-affinity constraint: this limits how high we can scale (need enough nodes)
- Explain the difference between 'required' (hard) and 'preferred' (soft) affinity: required blocks scheduling if violated
- Show the graceful shutdown flow: this prevents query failures during scale-down
- Connect to ResourceQuota: requests.cpu/memory are what quotas track

---

**END OF PART 1**

*Next: Part 2 (Sections 5-8: Reality Check, Alternatives, Anti-patterns, Common Failures)*
