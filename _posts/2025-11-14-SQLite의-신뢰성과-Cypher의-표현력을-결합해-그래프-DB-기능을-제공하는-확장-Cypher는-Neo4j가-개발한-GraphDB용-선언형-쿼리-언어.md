---
layout: post
title: "- SQLite의 신뢰성과 Cypher의 표현력을 결합해 그래프 DB 기능을 제공하는 확장 - Cypher는 Neo4j가 개발한 GraphDB용 선언형 쿼리 언어 ..."
date: 2025-11-14 21:33:57 +0900
categories: news
tags: [hada, mirror]
points: 0
author: GeekNews

hada_id: 24351
---

* **SQLite의 신뢰성과 Cypher의 표현력** 을 결합해 **그래프 DB 기능** 을 제공하는 확장 
    * Cypher는 Neo4j가 개발한 GraphDB용 선언형 쿼리 언어
  * **Cypher 쿼리 완전 지원** 을 목표로 하며, 현재 **CREATE, MATCH, WHERE, RETURN** 구문까지 동작
  * **SQL 함수 기반 그래프 조작** 지원 
    * `graph_node_add()`, `graph_edge_add()`, `graph_count_nodes()` 등 제공
  * **그래프 가상 테이블** 을 통해 SQLite 내부에서 노드와 엣지를 직접 관리
  * **기본 그래프 알고리듬** 포함 : 연결성 검사, 밀도 계산, 중심성(degree centrality) 지원
  * **Python 바인딩** 제공으로 Python 3.6+ 환경에서 직접 사용 가능
  * **멀티스레드 안전성** 확보로 병렬 환경에서도 안정적 동작
  * **아키텍처 구성**
    * **Virtual Table Interface** 로 SQLite와 통합
    * **Storage Engine** 은 JSON 기반 속성 저장 구조
    * **Cypher 실행 엔진** 은 파서 → 논리 플래너 → 물리 플래너 → 실행기 구조
    * **Volcano 모델 기반 이터레이터** 로 효율적 쿼리 실행
