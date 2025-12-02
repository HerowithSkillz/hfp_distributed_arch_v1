Markdown
# 🧠 Heterogeneous Distributed LLM Cluster

A custom-built, cost-effective distributed inference system that orchestrates Large Language Models (LLMs) across mixed consumer hardware. This project implements a **Django-based Load Balancer** to route traffic between a **Windows/NVIDIA** node and a **Linux/AMD** node via a unified API.

![System Status](https://img.shields.io/badge/System-Operational-green)
![Architecture](https://img.shields.io/badge/Architecture-Distributed-blue)
![GPU Support](https://img.shields.io/badge/GPU-CUDA%20%7C%20Vulkan-orange)

## 🏗️ Architecture

The system utilizes a **Microservices Architecture** where the central orchestrator (Django) abstracts the underlying hardware complexity from the client.

```mermaid
graph TD
    Client[User / Web Client] -->|POST /chat/| Django[Django Orchestrator]
    
    subgraph "Load Balancing Logic"
        Django -->|Check Health| Decision{Select Node}
    end
    
    Decision -->|CUDA Backend| NodeA[Windows 11 Worker]
    Decision -->|Vulkan Backend| NodeB[Kali Linux Worker]
    
    subgraph "Worker Node A (NVIDIA)"
        NodeA -->|llama.cpp| GPU1[NVIDIA GeForce MX (2GB)]
    end
    
    subgraph "Worker Node B (AMD)"
        NodeB -->|koboldcpp| GPU2[AMD Radeon R5 (2GB)]
    end
    
    NodeA -->|JSON Response| Django
    NodeB -->|JSON Response| Django
    Django -->|Unified Response| Client
```

## 🧩 The Hardware Challenge

The primary goal of this cluster was to run modern LLMs locally on legacy/budget consumer hardware with strict VRAM limits (2GB per node).

| Node | OS | GPU | VRAM | Engine | Backend |
|------|----|----|------|--------|---------|
| Worker A | Windows 11 | NVIDIA GeForce MX | 2GB | llama-server | CUDA |
| Worker B | Kali Linux | AMD Radeon R5 | 2GB | koboldcpp | Vulkan |

## 💡 Engineering Decision: Why not vLLM?

While vLLM is the industry standard for high-throughput serving, we deliberately chose llama.cpp and koboldcpp for this specific architecture. Here is why vLLM was rejected for this iteration:

- **The "Old AMD" Problem**: vLLM relies on ROCm for AMD support. Our Linux node uses an older Radeon R5 (GCN architecture) which is not supported by modern ROCm. We required Vulkan support to access the GPU, which koboldcpp provides flawlessly.
- **Extreme VRAM Constraints**: With only 2GB VRAM per node, standard FP16 loading is impossible. We needed highly efficient GGUF Quantization (Q4_K_M) to fit usable models into memory. llama.cpp libraries handle GGUF significantly better than vLLM in extremely low-memory environments.
- **OS Compatibility**: vLLM support for Windows is still experimental/limited compared to Linux. Our cluster is a hybrid environment (Windows + Linux), requiring tools that are stable on both.

## 🚀 Usage

### 1. Start the Worker Nodes

**Node A (Windows):**

```powershell
.\llama-server.exe -m model.gguf --host 0.0.0.0 --port 8080 --n-gpu-layers 99
```

**Node B (Linux):**

```bash
./koboldcpp-linux-x64 --model model.gguf --host 0.0.0.0 --port 5001 --usevulkan 1 --gpulayers 99
```

### 2. Start the Orchestrator

```bash
python manage.py runserver 0.0.0.0:8000
```

### 3. Send a Request

The system exposes a single unified endpoint. The load balancer automatically assigns the request to an available GPU.

```bash
curl -X POST http://localhost:8000/chat/ \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Explain distributed computing in simple terms."}'
```

## 🛠️ Features

- **Fault Tolerance**: If one laptop goes offline, the Django orchestrator detects the failure and routes traffic to the remaining node.
- **Hardware Agnostic**: Can mix and match any GPU (Intel/AMD/NVIDIA) as long as it exposes an OpenAI-compatible endpoint.
- **Private Network**: Runs entirely on a local Hotspot; no internet connection required for inference.
