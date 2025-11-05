package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/your-org/brain/control-plane/internal/services"
	"github.com/your-org/brain/control-plane/pkg/types"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/require"
)

type stubDispatcher struct {
	t           *testing.T
	payloads    services.PayloadStore
	resultBytes []byte
	dispatchErr error
	lastStep    *types.WorkflowStep
}

func (d *stubDispatcher) Dispatch(step *types.WorkflowStep, wait bool) (<-chan *services.DispatchResult, error) {
	d.lastStep = step
	if !wait {
		ch := make(chan *services.DispatchResult)
		close(ch)
		return ch, nil
	}

	ch := make(chan *services.DispatchResult, 1)
	if d.dispatchErr != nil {
		ch <- &services.DispatchResult{Step: step, Err: d.dispatchErr}
		close(ch)
		return ch, nil
	}

	record, err := d.payloads.SaveBytes(context.Background(), d.resultBytes)
	require.NoError(d.t, err)
	ch <- &services.DispatchResult{Step: step, ResultURI: &record.URI}
	close(ch)
	return ch, nil
}

func TestExecuteHandler_Success(t *testing.T) {
	gin.SetMode(gin.TestMode)

	storage := newTestExecutionStorage(&types.AgentNode{
		ID:      "node-1",
		BaseURL: "http://agent",
		Reasoners: []types.ReasonerDefinition{
			{ID: "reasoner-a"},
		},
	})
	payloads := services.NewFilePayloadStore(t.TempDir())
	dispatcher := &stubDispatcher{
		t:           t,
		payloads:    payloads,
		resultBytes: []byte(`{"answer":42}`),
	}

	router := gin.New()
	router.POST("/api/v1/execute/:target", ExecuteHandler(storage, dispatcher, payloads, nil))

	req := httptest.NewRequest(http.MethodPost, "/api/v1/execute/node-1.reasoner-a", strings.NewReader(`{"input":{"foo":"bar"}}`))
	req.Header.Set("Content-Type", "application/json")
	resp := httptest.NewRecorder()

	router.ServeHTTP(resp, req)

	require.Equal(t, http.StatusOK, resp.Code)

	var payload ExecuteResponse
	require.NoError(t, json.Unmarshal(resp.Body.Bytes(), &payload))
	require.Equal(t, types.ExecutionStatusSucceeded, payload.Status)
	require.Equal(t, "node-1", payload.NodeID)
	require.Equal(t, "reasoner", payload.Type)
	require.NotEmpty(t, payload.ExecutionID)
	require.NotEmpty(t, payload.RunID)

	resultMap, ok := payload.Result.(map[string]any)
	require.True(t, ok)
	require.Equal(t, float64(42), resultMap["answer"])

	require.NotNil(t, dispatcher.lastStep)
	require.NotNil(t, dispatcher.lastStep.InputURI)
	reader, err := payloads.Open(context.Background(), *dispatcher.lastStep.InputURI)
	require.NoError(t, err)
	defer reader.Close()
	saved, err := io.ReadAll(reader)
	require.NoError(t, err)
	var storedInput map[string]any
	require.NoError(t, json.Unmarshal(saved, &storedInput))
	require.Equal(t, map[string]any{"foo": "bar"}, storedInput)
}

func TestExecuteHandler_DispatchError(t *testing.T) {
	gin.SetMode(gin.TestMode)

	storage := newTestExecutionStorage(&types.AgentNode{
		ID:        "node-1",
		BaseURL:   "http://agent",
		Reasoners: []types.ReasonerDefinition{{ID: "reasoner-a"}},
	})
	payloads := services.NewFilePayloadStore(t.TempDir())
	dispatcher := &stubDispatcher{
		t:           t,
		payloads:    payloads,
		dispatchErr: assertError("boom"),
	}

	router := gin.New()
	router.POST("/api/v1/execute/:target", ExecuteHandler(storage, dispatcher, payloads, nil))

	req := httptest.NewRequest(http.MethodPost, "/api/v1/execute/node-1.reasoner-a", strings.NewReader(`{"input":{}}`))
	req.Header.Set("Content-Type", "application/json")
	resp := httptest.NewRecorder()

	router.ServeHTTP(resp, req)

	require.Equal(t, http.StatusOK, resp.Code)

	var payload ExecuteResponse
	require.NoError(t, json.Unmarshal(resp.Body.Bytes(), &payload))
	require.Equal(t, types.ExecutionStatusFailed, payload.Status)
	require.Contains(t, *payload.ErrorMessage, "boom")
	require.NotEmpty(t, payload.RunID)
}

func TestExecuteHandler_TargetNotFound(t *testing.T) {
	gin.SetMode(gin.TestMode)

	storage := newTestExecutionStorage(&types.AgentNode{ID: "node-1"})
	payloads := services.NewFilePayloadStore(t.TempDir())
	dispatcher := &stubDispatcher{t: t, payloads: payloads, resultBytes: []byte("{}")}

	router := gin.New()
	router.POST("/api/v1/execute/:target", ExecuteHandler(storage, dispatcher, payloads, nil))

	req := httptest.NewRequest(http.MethodPost, "/api/v1/execute/node-1.unknown", strings.NewReader(`{"input":{}}`))
	req.Header.Set("Content-Type", "application/json")
	resp := httptest.NewRecorder()

	router.ServeHTTP(resp, req)

	require.Equal(t, http.StatusNotFound, resp.Code)
}

func TestExecuteAsyncHandler_ReturnsAccepted(t *testing.T) {
	gin.SetMode(gin.TestMode)

	storage := newTestExecutionStorage(&types.AgentNode{
		ID:        "node-1",
		BaseURL:   "http://agent",
		Reasoners: []types.ReasonerDefinition{{ID: "reasoner-a"}},
	})
	payloads := services.NewFilePayloadStore(t.TempDir())
	dispatcher := &stubDispatcher{t: t, payloads: payloads}

	router := gin.New()
	router.POST("/api/v1/execute/async/:target", ExecuteAsyncHandler(storage, dispatcher, payloads, nil))

	req := httptest.NewRequest(http.MethodPost, "/api/v1/execute/async/node-1.reasoner-a", strings.NewReader(`{"input":{"abc":123}}`))
	req.Header.Set("Content-Type", "application/json")
	resp := httptest.NewRecorder()

	router.ServeHTTP(resp, req)

	require.Equal(t, http.StatusAccepted, resp.Code)

	var payload AsyncExecuteResponse
	require.NoError(t, json.Unmarshal(resp.Body.Bytes(), &payload))
	require.NotEmpty(t, payload.ExecutionID)
	require.NotEmpty(t, payload.RunID)
	require.Equal(t, servicesStepStatusPending, payload.Status)

	storedExec, err := storage.GetWorkflowExecution(context.Background(), payload.ExecutionID)
	require.NoError(t, err)
	require.NotNil(t, storedExec)
	require.Equal(t, "node-1", storedExec.AgentNodeID)
}

func TestExecuteAsyncHandler_InvalidJSON(t *testing.T) {
	gin.SetMode(gin.TestMode)

	storage := newTestExecutionStorage(&types.AgentNode{
		ID:        "node-1",
		BaseURL:   "http://agent",
		Reasoners: []types.ReasonerDefinition{{ID: "reasoner-a"}},
	})
	payloads := services.NewFilePayloadStore(t.TempDir())
	dispatcher := &stubDispatcher{t: t, payloads: payloads}

	router := gin.New()
	router.POST("/api/v1/execute/async/:target", ExecuteAsyncHandler(storage, dispatcher, payloads, nil))

	req := httptest.NewRequest(http.MethodPost, "/api/v1/execute/async/node-1.reasoner-a", strings.NewReader("not-json"))
	req.Header.Set("Content-Type", "application/json")
	resp := httptest.NewRecorder()

	router.ServeHTTP(resp, req)

	require.Equal(t, http.StatusBadRequest, resp.Code)
}

func TestGetExecutionStatusHandler_ReturnsResult(t *testing.T) {
	gin.SetMode(gin.TestMode)

	storage := newTestExecutionStorage(&types.AgentNode{ID: "node-1"})
	payloads := services.NewFilePayloadStore(t.TempDir())
	result, err := payloads.SaveBytes(context.Background(), []byte(`{"ok":true}`))
	require.NoError(t, err)

	exec := &types.WorkflowExecution{
		WorkflowID:  "wf-1",
		ExecutionID: "exec-1",
		AgentNodeID: "node-1",
		ReasonerID:  "reasoner-a",
		Status:      servicesStepStatusSucceeded,
		StartedAt:   time.Now().Add(-time.Minute),
		CompletedAt: ptrTime(time.Now()),
		DurationMS:  ptrInt64(42),
	}
	require.NoError(t, storage.StoreWorkflowExecution(context.Background(), exec))

	step := &types.WorkflowStep{
		StepID:    "exec-1",
		RunID:     "wf-1",
		Status:    servicesStepStatusSucceeded,
		ResultURI: &result.URI,
	}
	require.NoError(t, storage.StoreWorkflowStep(context.Background(), step))

	router := gin.New()
	router.GET("/api/v1/executions/:execution_id", GetExecutionStatusHandler(storage, payloads, nil))

	req := httptest.NewRequest(http.MethodGet, "/api/v1/executions/exec-1", nil)
	resp := httptest.NewRecorder()

	router.ServeHTTP(resp, req)

	require.Equal(t, http.StatusOK, resp.Code)

	var payload ExecutionStatusResponse
	require.NoError(t, json.Unmarshal(resp.Body.Bytes(), &payload))
	require.Equal(t, "exec-1", payload.ExecutionID)
	resultMap, ok := payload.Result.(map[string]any)
	require.True(t, ok)
	require.Equal(t, true, resultMap["ok"])
}

func TestBatchExecutionStatusHandler_MixedResults(t *testing.T) {
	gin.SetMode(gin.TestMode)

	storage := newTestExecutionStorage(&types.AgentNode{ID: "node-1"})
	payloads := services.NewFilePayloadStore(t.TempDir())

	exec := &types.WorkflowExecution{
		WorkflowID:  "wf-1",
		ExecutionID: "exec-ok",
		AgentNodeID: "node-1",
		ReasonerID:  "reasoner-a",
		Status:      servicesStepStatusSucceeded,
		StartedAt:   time.Now().Add(-time.Second),
		CompletedAt: ptrTime(time.Now()),
	}
	require.NoError(t, storage.StoreWorkflowExecution(context.Background(), exec))

	router := gin.New()
	router.POST("/api/v1/executions/batch-status", BatchExecutionStatusHandler(storage, payloads, nil))

	body := `{"execution_ids":["exec-ok","exec-missing"]}`
	req := httptest.NewRequest(http.MethodPost, "/api/v1/executions/batch-status", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	resp := httptest.NewRecorder()

	router.ServeHTTP(resp, req)

	require.Equal(t, http.StatusOK, resp.Code)

	var payload BatchStatusResponse
	require.NoError(t, json.Unmarshal(resp.Body.Bytes(), &payload))
	require.Equal(t, servicesStepStatusSucceeded, payload["exec-ok"].Status)
	require.Equal(t, "not_found", payload["exec-missing"].Status)
}

func assertError(msg string) error {
	return fmt.Errorf(msg)
}
