const STEPS = ['User Info', 'Handwriting', 'Speech', 'Eye Tracking', 'Cognitive', 'Report'];

export default function ProgressStepper({ currentStep }) {
  const stepIndex = STEPS.findIndex((s) => s.toLowerCase().replace(/\s/g, '') === currentStep);
  const activeIndex = stepIndex >= 0 ? stepIndex : 0;

  return (
    <div className="stepper">
      {STEPS.map((label, index) => {
        const isActive = index === activeIndex;
        const isComplete = index < activeIndex;
        return (
          <div key={label} className="stepper-item">
            <div
              className={[
                'stepper-pill',
                isActive ? 'stepper-pill-active' : '',
                isComplete ? 'stepper-pill-complete' : '',
              ]
                .filter(Boolean)
                .join(' ')}
            >
              <span className="stepper-index">{index + 1}</span>
              <span className="stepper-label">{label}</span>
            </div>
            {index < STEPS.length - 1 && <div className="stepper-rail" />}
          </div>
        );
      })}
    </div>
  );
}
