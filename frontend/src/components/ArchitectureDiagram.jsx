import { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

export function ArchitectureDiagram() {
  const diagramRef = useRef(null);

  useEffect(() => {
    if (diagramRef.current) {
      mermaid.contentLoaded();
      mermaid.run();
    }
  }, []);

  const diagramDefinition = `graph TB
    subgraph "User Layer"
        USER[User Query]
    end
    
    subgraph "Planning Brain"
        LG[LangGraph Planner<br/>Intelligent Decision Making]
    end
    
    subgraph "Orchestration"
        ORCH[Orchestrator<br/>Coordinates Execution]
        EVAL[Evaluator<br/>Quality Check & Replan]
    end
    
    subgraph "Message Queue"
        RMQ[RabbitMQ<br/>Distributed Task Queue]
    end
    
    subgraph "Execution Workers"
        W1[Worker 1]
        W2[Worker 2]
        W3[Worker N]
    end
    
    subgraph "Tools"
        VS[Vector Search<br/>ChromaDB]
        GQ[Graph Query<br/>Neo4j]
        EM[Entity Matching<br/>Semantic]
        LLM[Reasoning<br/>Groq LLM]
    end
    
    subgraph "State Storage"
        REDIS[Redis<br/>Results & State]
    end
    
    USER --> LG
    LG -->|Agent Plan| ORCH
    ORCH -->|Publish Steps| RMQ
    
    RMQ --> W1
    RMQ --> W2
    RMQ --> W3
    
    W1 --> VS
    W1 --> GQ
    W2 --> EM
    W2 --> LLM
    W3 --> VS
    
    W1 -->|Store Results| REDIS
    W2 -->|Store Results| REDIS
    W3 -->|Store Results| REDIS
    
    REDIS --> ORCH
    ORCH --> EVAL
    EVAL -->|Replan if Needed| LG
    EVAL -->|Complete| USER
    
    style LG fill:#9C27B0
    style ORCH fill:#FF9800
    style RMQ fill:#2196F3
    style W1 fill:#4CAF50
    style W2 fill:#4CAF50
    style W3 fill:#4CAF50
    style EVAL fill:#E91E63`;

  return (
    <div className="w-full bg-gray-900 border border-gray-800 rounded-xl p-6 overflow-hidden">
      <h3 className="text-lg font-mono text-gray-400 mb-4">SYSTEM ARCHITECTURE</h3>
      <div 
        ref={diagramRef}
        className="mermaid overflow-x-auto max-w-full bg-gray-950 rounded-lg p-4"
        style={{ minHeight: '600px' }}
      >
        {diagramDefinition}
      </div>
    </div>
  );
}
