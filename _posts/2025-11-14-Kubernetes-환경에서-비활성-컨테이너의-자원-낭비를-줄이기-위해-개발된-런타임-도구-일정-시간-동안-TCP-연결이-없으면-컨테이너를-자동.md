---
layout: post
title: "- Kubernetes 환경에서 비활성 컨테이너의 자원 낭비를 줄이기 위해 개발된 런타임 도구 - 일정 시간 동안 TCP 연결이 없으면 컨테이너를 자동..."
date: 2025-11-14 21:31:13 +0900
categories: news
tags: [hada, mirror]
points: 0
author: GeekNews

hada_id: 24330
---

Kubernetes 환경
에서
비활성 컨테이너의 자원 낭비
를 줄이기 위해 개발된
런타임 도구
일정 시간 동안 TCP 연결이 없으면 컨테이너를 자동으로
디스크에 체크포인트 저장
containerd shim
형태로 동작하며, 컨테이너의 메모리 상태를 저장 후 종료하고, 이후 첫 연결 시
수 밀리초 내 복원
복원 시 애플리케이션의
모든 상태가 그대로 복구
되어 사용자 입장에서 지연이 거의 없음
eBPF 기반 리디렉션
을 사용해 TCP 패킷을 프록시로 전달하고, 복원 완료 후에는 직접 연결로 전환
CRIU - Checkpoint and Restore in Userspace
를 이용해 체크포인트 및 복원 수행
활성화 시퀀스(activation sequence)
를 통해 첫 요청 시 자동 복원되는 흐름 제공
최근 TCP 활동을 추적
해 빈번한 중단·복원을 방지하는 지능형 대기 로직 포함
Kubernetes 상에서는 컨테이너가 계속 실행 중인 것처럼 인식되어
런타임 재시작 방지
kubectl exec
명령 시 자동 복원되어 일반 컨테이너처럼 접근 가능
각 shim 프로세스가
메트릭을 수집
하고, 노드 단위의
zeropod-manager
가 이를 통합해 HTTP 엔드포인트로 노출
클러스터가 지원할 경우
리소스 요청을 동적으로 조정
하는
in-place scaling
기능 제공
노드 드레이닝 시
스케일 다운된 Pod를 다른 노드로 마이그레이션
가능
실험적 기능으로
라이브 마이그레이션
도 지원
저트래픽 서비스, 개발·스테이징 환경, Heroku 유사 플랫폼의 저가 tier, 정적 사이트의 백엔드 구성
등에 적합
대부분의 프로그램이 별도 수정 없이 동작하며,
containerd 로그를 통해 CRIU 오류 분석 가능
