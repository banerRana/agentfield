package handlers

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/your-org/brain/control-plane/internal/events"
	"github.com/your-org/brain/control-plane/pkg/types"
)

type testExecutionStorage struct {
	mu                        sync.Mutex
	agent                     *types.AgentNode
	executions                map[string]*types.WorkflowExecution
	runs                      map[string]*types.WorkflowRun
	steps                     map[string]*types.WorkflowStep
	eventBus                  *events.ExecutionEventBus
	workflowExecutionEventBus *events.EventBus[*types.WorkflowExecutionEvent]
	workflowRunEventBus       *events.EventBus[*types.WorkflowRunEvent]
	updateCh                  chan string
}

func newTestExecutionStorage(agent *types.AgentNode) *testExecutionStorage {
	return &testExecutionStorage{
		agent:                     agent,
		executions:                make(map[string]*types.WorkflowExecution),
		runs:                      make(map[string]*types.WorkflowRun),
		steps:                     make(map[string]*types.WorkflowStep),
		eventBus:                  events.NewExecutionEventBus(),
		workflowExecutionEventBus: events.NewEventBus[*types.WorkflowExecutionEvent](),
		workflowRunEventBus:       events.NewEventBus[*types.WorkflowRunEvent](),
		updateCh:                  make(chan string, 10),
	}
}

func (s *testExecutionStorage) GetAgent(ctx context.Context, id string) (*types.AgentNode, error) {
	if s.agent != nil && s.agent.ID == id {
		return s.agent, nil
	}
	return nil, fmt.Errorf("agent %s not found", id)
}

func (s *testExecutionStorage) StoreWorkflowExecution(ctx context.Context, execution *types.WorkflowExecution) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if execution == nil {
		return fmt.Errorf("execution cannot be nil")
	}
	s.executions[execution.ExecutionID] = execution
	select {
	case s.updateCh <- execution.ExecutionID:
	default:
	}
	return nil
}

func (s *testExecutionStorage) UpdateWorkflowExecution(ctx context.Context, executionID string, updateFunc func(*types.WorkflowExecution) (*types.WorkflowExecution, error)) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	existing, ok := s.executions[executionID]
	if !ok {
		return fmt.Errorf("execution %s not found", executionID)
	}

	if updateFunc == nil {
		return fmt.Errorf("updateFunc cannot be nil")
	}

	updated, err := updateFunc(existing)
	if err != nil {
		return err
	}
	if updated != nil {
		s.executions[executionID] = updated
	}
	select {
	case s.updateCh <- executionID:
	default:
	}
	return nil
}

func (s *testExecutionStorage) GetWorkflowExecution(ctx context.Context, executionID string) (*types.WorkflowExecution, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	execution, ok := s.executions[executionID]
	if !ok {
		return nil, nil
	}
	return execution, nil
}

func (s *testExecutionStorage) StoreWorkflowRun(ctx context.Context, run *types.WorkflowRun) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if run == nil {
		return fmt.Errorf("run cannot be nil")
	}
	s.runs[run.RunID] = run
	return nil
}

func (s *testExecutionStorage) GetWorkflowRun(ctx context.Context, runID string) (*types.WorkflowRun, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	run, ok := s.runs[runID]
	if !ok {
		return nil, nil
	}
	return run, nil
}

func (s *testExecutionStorage) UpdateWorkflowRun(ctx context.Context, runID string, updateFunc func(*types.WorkflowRun) (*types.WorkflowRun, error)) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	run, ok := s.runs[runID]
	if !ok {
		return fmt.Errorf("run %s not found", runID)
	}
	updated, err := updateFunc(run)
	if err != nil {
		return err
	}
	if updated != nil {
		s.runs[runID] = updated
	}
	return nil
}

func (s *testExecutionStorage) QueryWorkflowRuns(ctx context.Context, filters types.WorkflowRunFilters) ([]*types.WorkflowRun, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	var results []*types.WorkflowRun
	for _, run := range s.runs {
		if filters.RunID != nil && *filters.RunID != run.RunID {
			continue
		}
		results = append(results, run)
	}
	return results, nil
}

func (s *testExecutionStorage) CountWorkflowRuns(ctx context.Context, filters types.WorkflowRunFilters) (int, error) {
	runs, _ := s.QueryWorkflowRuns(ctx, filters)
	return len(runs), nil
}

func (s *testExecutionStorage) StoreWorkflowStep(ctx context.Context, step *types.WorkflowStep) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if step == nil {
		return fmt.Errorf("step cannot be nil")
	}
	s.steps[step.StepID] = step
	return nil
}

func (s *testExecutionStorage) StoreWorkflowRunAndStep(ctx context.Context, run *types.WorkflowRun, step *types.WorkflowStep) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if run == nil {
		return fmt.Errorf("run cannot be nil")
	}
	if step == nil {
		return fmt.Errorf("step cannot be nil")
	}
	s.runs[run.RunID] = run
	s.steps[step.StepID] = step
	return nil
}

func (s *testExecutionStorage) GetWorkflowStep(ctx context.Context, stepID string) (*types.WorkflowStep, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	step, ok := s.steps[stepID]
	if !ok {
		return nil, nil
	}
	return step, nil
}

func (s *testExecutionStorage) GetExecutionEventBus() *events.ExecutionEventBus {
	return s.eventBus
}

func (s *testExecutionStorage) GetWorkflowExecutionEventBus() *events.EventBus[*types.WorkflowExecutionEvent] {
	return s.workflowExecutionEventBus
}

func (s *testExecutionStorage) GetWorkflowRunEventBus() *events.EventBus[*types.WorkflowRunEvent] {
	return s.workflowRunEventBus
}

func (s *testExecutionStorage) RegisterExecutionWebhook(ctx context.Context, webhook *types.ExecutionWebhook) error {
	return nil
}

func ptrTime(t time.Time) *time.Time {
	return &t
}

func ptrInt64(v int64) *int64 {
	return &v
}
