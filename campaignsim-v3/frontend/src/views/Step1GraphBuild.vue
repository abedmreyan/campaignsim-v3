<template>
  <div class="s1-root">

    <!-- ── Entry phase ─────────────────────────────────────────────────── -->
    <template v-if="phase === 'entry'">
      <div class="s1-entry-layout">
        <div class="s1-section-header">
          <p class="eyebrow">Step 1 · Brand Intelligence</p>
          <h1 class="s1-section-header__title">Build your brand intelligence map</h1>
          <p class="s1-section-header__lead">
            Start by telling us about your brand. Our AI extracts products, audiences, channels, and values into a structured knowledge graph that powers your campaign simulations.
          </p>
        </div>

        <div class="s1-entry-cards">
          <!-- AI Guided (primary) -->
          <button class="s1-entry-card s1-entry-card--primary" @click="inputMethod = 'guided'">
            <span class="s1-entry-card__badge">Recommended</span>
            <div class="s1-entry-card__icon" style="background:rgba(10,191,173,0.12);color:var(--color-accent)">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.22 4.22l2.12 2.12M17.66 17.66l2.12 2.12M2 12h3M19 12h3M4.22 19.78l2.12-2.12M17.66 6.34l2.12-2.12"/>
              </svg>
            </div>
            <h2 class="s1-entry-card__title">AI-Guided Setup</h2>
            <p class="s1-entry-card__desc">Answer a few questions and our AI builds a comprehensive intelligence map — no document needed.</p>
            <ul class="s1-entry-card__list">
              <li>5-minute guided questionnaire</li>
              <li>Live intelligence preview</li>
              <li>No document required</li>
            </ul>
            <span class="s1-entry-card__cta">Get started <span aria-hidden="true">→</span></span>
          </button>

          <!-- Upload brief -->
          <button class="s1-entry-card" @click="inputMethod = 'upload'">
            <div class="s1-entry-card__icon" style="background:rgba(99,102,241,0.12);color:#818cf8">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><polyline points="9 15 12 12 15 15"/>
              </svg>
            </div>
            <h2 class="s1-entry-card__title">Upload Brief</h2>
            <p class="s1-entry-card__desc">Upload your existing campaign brief, strategy doc, or pitch deck and AI extracts the intelligence.</p>
            <ul class="s1-entry-card__list">
              <li>PDF or text file</li>
              <li>Up to 10 MB</li>
              <li>Automatic entity extraction</li>
            </ul>
            <span class="s1-entry-card__cta">Upload file <span aria-hidden="true">→</span></span>
          </button>

          <!-- Import URL (disabled) -->
          <div class="s1-entry-card s1-entry-card--disabled" aria-disabled="true">
            <span class="s1-entry-card__badge s1-entry-card__badge--muted">Coming soon</span>
            <div class="s1-entry-card__icon" style="background:rgba(255,255,255,0.04);color:var(--color-text-ghost)">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
              </svg>
            </div>
            <h2 class="s1-entry-card__title">Import from URL</h2>
            <p class="s1-entry-card__desc">Connect your website, CRM, or content hub and we'll extract brand intelligence automatically.</p>
            <ul class="s1-entry-card__list">
              <li>Website crawling</li>
              <li>HubSpot / Salesforce</li>
              <li>Auto-sync on demand</li>
            </ul>
          </div>
        </div>
      </div>
    </template>

    <!-- ── Guided phase ─────────────────────────────────────────────────── -->
    <template v-else-if="phase === 'guided'">
      <div class="s1-guided-layout">

        <!-- Left: stepper form -->
        <div class="s1-guided-primary">
          <!-- Eyebrow + title -->
          <div class="s1-section-header">
            <div class="s1-section-header__row">
              <div>
                <p class="eyebrow">Step 1 · Brand Intelligence</p>
                <h1 class="s1-section-header__title">Tell us about your brand</h1>
              </div>
              <button class="s1-back-link" @click="inputMethod = null">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M9 11L5 7l4-4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
                Back
              </button>
            </div>
          </div>

          <!-- Section stepper -->
          <div class="s1-stepper" role="tablist" aria-label="Questionnaire sections">
            <button
              v-for="(sec, i) in guidedSections"
              :key="i"
              class="s1-stepper__item"
              :class="{
                's1-stepper__item--active': guidedSection === i,
                's1-stepper__item--done': isSectionDone(i),
              }"
              role="tab"
              :aria-selected="guidedSection === i"
              @click="guidedSection = i"
            >
              <span class="s1-stepper__pip" aria-hidden="true">
                <svg v-if="isSectionDone(i)" width="9" height="9" viewBox="0 0 10 10" fill="none"><path d="M1.5 5L4 7.5L8.5 2.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                <span v-else>{{ i + 1 }}</span>
              </span>
              <span class="s1-stepper__label">{{ sec.label }}</span>
            </button>
          </div>

          <!-- Section 0: Brand Identity -->
          <div v-if="guidedSection === 0" class="s1-guided-section" role="tabpanel">
            <p class="s1-guided-section__title">Brand Identity</p>
            <p class="s1-guided-section__sub">The foundation of your intelligence map. Be specific — this shapes every downstream simulation.</p>
            <div class="s1-form-grid">
              <div class="s1-form-field">
                <label class="s1-form-label">Brand name <span class="s1-required">*</span></label>
                <input v-model="guidedForm.brandName" class="s1-form-input" type="text" placeholder="e.g. Acme Corp" />
              </div>
              <div class="s1-form-field">
                <label class="s1-form-label">Industry <span class="s1-required">*</span></label>
                <select v-model="guidedForm.industry" class="s1-form-input s1-form-select">
                  <option value="" disabled>Select an industry</option>
                  <option v-for="ind in INDUSTRIES" :key="ind" :value="ind">{{ ind }}</option>
                </select>
              </div>
              <div class="s1-form-field s1-form-field--full">
                <label class="s1-form-label">Value proposition <span class="s1-required">*</span></label>
                <textarea v-model="guidedForm.valueProposition" class="s1-form-textarea" rows="3" placeholder="What unique value does your brand deliver? e.g. 'We help mid-market retailers cut operational costs by 30% through AI-driven inventory management.'" />
              </div>
              <div class="s1-form-field s1-form-field--full">
                <label class="s1-form-label">Brand values <span class="s1-form-hint">(optional — comma-separated)</span></label>
                <input v-model="guidedForm.brandValues" class="s1-form-input" type="text" placeholder="e.g. Innovation, Sustainability, Trust, Transparency" />
              </div>
            </div>
            <div class="s1-section-nav">
              <span></span>
              <button class="s1-section-nav__next" :disabled="!isSectionDone(0)" @click="guidedSection = 1">Products & Services <span aria-hidden="true">→</span></button>
            </div>
          </div>

          <!-- Section 1: Products & Services -->
          <div v-else-if="guidedSection === 1" class="s1-guided-section" role="tabpanel">
            <p class="s1-guided-section__title">Products & Services</p>
            <p class="s1-guided-section__sub">List the key offerings you want to include in the simulation. Add as many as relevant.</p>
            <div class="s1-product-list">
              <div v-for="(product, i) in guidedForm.products" :key="i" class="s1-product-row">
                <div class="s1-product-row__fields">
                  <input v-model="product.name" class="s1-form-input" type="text" :placeholder="`Product or service name (e.g. ${i === 0 ? 'ProPlan Subscription' : i === 1 ? 'Enterprise License' : 'Add-on Package'})`" />
                  <input v-model="product.description" class="s1-form-input" type="text" placeholder="Brief description (optional)" />
                </div>
                <button v-if="guidedForm.products.length > 1" class="s1-product-row__remove" @click="removeProduct(i)" aria-label="Remove product">
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M2 7h10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
                </button>
              </div>
            </div>
            <button v-if="guidedForm.products.length < 8" class="s1-add-row" @click="addProduct">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M7 2v10M2 7h10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
              Add another product
            </button>
            <div class="s1-section-nav">
              <button class="s1-section-nav__back" @click="guidedSection = 0"><span aria-hidden="true">←</span> Brand Identity</button>
              <button class="s1-section-nav__next" :disabled="!isSectionDone(1)" @click="guidedSection = 2">Target Audience <span aria-hidden="true">→</span></button>
            </div>
          </div>

          <!-- Section 2: Target Audience -->
          <div v-else-if="guidedSection === 2" class="s1-guided-section" role="tabpanel">
            <p class="s1-guided-section__title">Target Audience</p>
            <p class="s1-guided-section__sub">Define up to 3 audience segments. These become the basis for synthetic persona generation in Step 2.</p>
            <div class="s1-audience-list">
              <div v-for="(aud, i) in guidedForm.audiences" :key="i" class="s1-audience-card">
                <div class="s1-audience-card__head">
                  <span class="s1-audience-card__num">Segment {{ i + 1 }}</span>
                  <button v-if="guidedForm.audiences.length > 1" class="s1-product-row__remove" @click="removeAudience(i)" aria-label="Remove segment">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M2 7h10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
                  </button>
                </div>
                <div class="s1-form-grid">
                  <div class="s1-form-field">
                    <label class="s1-form-label">Segment name <span class="s1-required">*</span></label>
                    <input v-model="aud.name" class="s1-form-input" type="text" :placeholder="i === 0 ? 'e.g. Young Professionals' : i === 1 ? 'e.g. Small Business Owners' : 'e.g. Enterprise Decision Makers'" />
                  </div>
                  <div class="s1-form-field">
                    <label class="s1-form-label">Age range <span class="s1-form-hint">(optional)</span></label>
                    <input v-model="aud.ageRange" class="s1-form-input" type="text" placeholder="e.g. 25–40" />
                  </div>
                  <div class="s1-form-field s1-form-field--full">
                    <label class="s1-form-label">Psychographics & pain points <span class="s1-form-hint">(optional)</span></label>
                    <textarea v-model="aud.description" class="s1-form-textarea" rows="2" placeholder="e.g. Tech-savvy, budget-conscious, values speed and reliability, frustrated by complex onboarding" />
                  </div>
                </div>
              </div>
            </div>
            <button v-if="guidedForm.audiences.length < 3" class="s1-add-row" @click="addAudience">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M7 2v10M2 7h10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
              Add audience segment
            </button>
            <div class="s1-section-nav">
              <button class="s1-section-nav__back" @click="guidedSection = 1"><span aria-hidden="true">←</span> Products</button>
              <button class="s1-section-nav__next" :disabled="!isSectionDone(2)" @click="guidedSection = 3">Marketing Channels <span aria-hidden="true">→</span></button>
            </div>
          </div>

          <!-- Section 3: Marketing Channels -->
          <div v-else-if="guidedSection === 3" class="s1-guided-section" role="tabpanel">
            <p class="s1-guided-section__title">Marketing Channels</p>
            <p class="s1-guided-section__sub">Select all channels your brand uses or plans to use. These become nodes in your intelligence graph.</p>
            <div class="s1-chip-grid" role="group" aria-label="Marketing channels">
              <button
                v-for="ch in CHANNELS"
                :key="ch"
                class="s1-chip"
                :class="{ 's1-chip--selected': guidedForm.channels.includes(ch) }"
                type="button"
                :aria-pressed="guidedForm.channels.includes(ch)"
                @click="toggleChip(guidedForm.channels, ch)"
              >
                {{ ch }}
              </button>
            </div>
            <div class="s1-section-nav">
              <button class="s1-section-nav__back" @click="guidedSection = 2"><span aria-hidden="true">←</span> Audience</button>
              <button class="s1-section-nav__next" :disabled="!isSectionDone(3)" @click="guidedSection = 4">Content Formats <span aria-hidden="true">→</span></button>
            </div>
          </div>

          <!-- Section 4: Content Formats -->
          <div v-else-if="guidedSection === 4" class="s1-guided-section" role="tabpanel">
            <p class="s1-guided-section__title">Content Formats</p>
            <p class="s1-guided-section__sub">Which content types does your brand produce or plan to test? Select all that apply.</p>
            <div class="s1-chip-grid" role="group" aria-label="Content formats">
              <button
                v-for="fmt in FORMATS"
                :key="fmt"
                class="s1-chip"
                :class="{ 's1-chip--selected': guidedForm.formats.includes(fmt) }"
                type="button"
                :aria-pressed="guidedForm.formats.includes(fmt)"
                @click="toggleChip(guidedForm.formats, fmt)"
              >
                {{ fmt }}
              </button>
            </div>
            <div class="s1-section-nav">
              <button class="s1-section-nav__back" @click="guidedSection = 3"><span aria-hidden="true">←</span> Channels</button>
              <button class="s1-section-nav__next" :disabled="!isSectionDone(4)" @click="guidedSection = 5">Campaign Objective <span aria-hidden="true">→</span></button>
            </div>
          </div>

          <!-- Section 5: Campaign Objective + final review -->
          <div v-else-if="guidedSection === 5" class="s1-guided-section" role="tabpanel">
            <p class="s1-guided-section__title">Campaign Objective</p>
            <p class="s1-guided-section__sub">What's the primary goal of this campaign simulation? This shapes how the AI models variant performance.</p>
            <div class="s1-objective-grid">
              <button
                v-for="obj in OBJECTIVES"
                :key="obj.value"
                class="s1-objective-card"
                :class="{ 's1-objective-card--selected': guidedForm.objective === obj.value }"
                type="button"
                @click="guidedForm.objective = obj.value"
              >
                <strong>{{ obj.label }}</strong>
                <p>{{ obj.desc }}</p>
                <span v-if="guidedForm.objective === obj.value" class="s1-objective-card__check" aria-hidden="true">
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 6L5 9L10 3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </span>
              </button>
            </div>

            <ErrorState v-if="store.graph.error" :message="store.graph.error" />

            <div class="s1-section-nav s1-section-nav--final">
              <button class="s1-section-nav__back" @click="guidedSection = 4"><span aria-hidden="true">←</span> Content Formats</button>
              <AppButton size="lg" :disabled="!guidedIsComplete" :loading="store.graph.loading" @click="runGuided">
                Build intelligence map
              </AppButton>
            </div>
            <p class="s1-upload-hint" style="margin-top:0.5rem">AI extracts brand entities and maps relationships — takes 30–60 seconds.</p>
          </div>
        </div>

        <!-- Right: live intelligence preview -->
        <aside class="s1-guided-secondary">
          <div class="s1-preview-live">
            <p class="s1-preview-live__title">Intelligence preview</p>
            <p class="s1-preview-live__sub">Updates as you fill in your brand details</p>

            <div class="s1-preview-live__progress">
              <div class="s1-progress-track">
                <span class="s1-progress-fill" :style="{ width: `${guidedCompletionPercent}%` }"></span>
              </div>
              <span class="s1-progress-pct">{{ guidedCompletionPercent }}%</span>
            </div>

            <div v-if="guidedPreview.length" class="s1-preview-live__entities">
              <div
                v-for="(grp, i) in guidedPreviewGrouped"
                :key="i"
                class="s1-preview-group"
              >
                <div class="s1-preview-group__head">
                  <span class="s1-preview-group__icon" :style="{ background: grp.bgColor, color: grp.fgColor }" aria-hidden="true">
                    <component :is="grp.iconComponent" />
                  </span>
                  <span class="s1-preview-group__label">{{ grp.label }}</span>
                  <span class="s1-preview-group__count">{{ grp.items.length }}</span>
                </div>
                <div class="s1-preview-group__tags">
                  <span v-for="item in grp.items" :key="item" class="s1-preview-tag" :style="{ borderColor: grp.fgColor + '33', color: grp.fgColor }">{{ item }}</span>
                </div>
              </div>
            </div>
            <div v-else class="s1-preview-live__empty">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="3"/><path d="M12 2v2M12 20v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M2 12h2M20 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
              </svg>
              <p>Entities will appear here as you fill in your brand details.</p>
            </div>
          </div>

          <!-- AI Suggestions panel -->
          <div
            v-if="aiSuggestions !== null || section0Complete"
            class="s1-ai-suggestions"
            :class="{ 's1-ai-suggestions--loading': aiSuggestions === 'loading' }"
          >
            <div class="s1-ai-suggestions__header">
              <span class="s1-ai-badge" aria-label="AI suggestions">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z"/>
                </svg>
                AI Suggestions
              </span>
              <span v-if="aiSuggestions === 'loading'" class="s1-ai-status">Analyzing…</span>
              <span v-else-if="aiSuggestions && guidedSection >= 1" class="s1-ai-status s1-ai-status--ready">Ready</span>
            </div>

            <!-- Loading shimmer -->
            <template v-if="aiSuggestions === 'loading'">
              <div class="s1-ai-shimmer">
                <span class="s1-ai-shimmer__bar" style="width:70%"></span>
                <span class="s1-ai-shimmer__bar" style="width:55%"></span>
                <span class="s1-ai-shimmer__bar" style="width:80%"></span>
              </div>
            </template>

            <!-- Suggestions by section -->
            <template v-else-if="typeof aiSuggestions === 'object' && aiSuggestions !== null">
              <!-- Section 0 done but not moved on yet -->
              <p v-if="guidedSection === 0" class="s1-ai-hint">
                Complete Brand Identity and move to the next section to see AI-generated suggestions.
              </p>

              <!-- Section 1: Products -->
              <template v-if="guidedSection === 1 && aiSuggestions.products">
                <p class="s1-ai-category__label">Suggested products</p>
                <div class="s1-ai-chips">
                  <button
                    v-for="p in aiSuggestions.products"
                    :key="p.name"
                    class="s1-ai-chip"
                    :class="{ 's1-ai-chip--used': isProductAccepted(p.name) }"
                    :title="p.description || undefined"
                    type="button"
                    @click="acceptProductSuggestion(p)"
                  >
                    <span>{{ p.name }}</span>
                    <svg v-if="!isProductAccepted(p.name)" width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M6 2v8M2 6h8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
                    <svg v-else width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M2 6l3 3 5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  </button>
                </div>
              </template>

              <!-- Section 2: Audiences -->
              <template v-if="guidedSection === 2 && aiSuggestions.audiences">
                <p class="s1-ai-category__label">Suggested segments</p>
                <div class="s1-ai-chips">
                  <button
                    v-for="a in aiSuggestions.audiences"
                    :key="a.name"
                    class="s1-ai-chip"
                    :class="{ 's1-ai-chip--used': isAudienceAccepted(a.name) }"
                    :title="[a.ageRange && `Age ${a.ageRange}`, a.description].filter(Boolean).join(' · ') || undefined"
                    type="button"
                    @click="acceptAudienceSuggestion(a)"
                  >
                    <span>{{ a.name }}</span>
                    <svg v-if="!isAudienceAccepted(a.name)" width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M6 2v8M2 6h8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
                    <svg v-else width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M2 6l3 3 5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  </button>
                </div>
              </template>

              <!-- Section 3: Channels -->
              <template v-if="guidedSection === 3 && aiSuggestions.channels">
                <div class="s1-ai-category__row">
                  <p class="s1-ai-category__label">Suggested channels</p>
                  <button class="s1-ai-accept-all" type="button" @click="acceptAllChannels">Accept all</button>
                </div>
                <div class="s1-ai-chips">
                  <button
                    v-for="c in aiSuggestions.channels"
                    :key="c"
                    class="s1-ai-chip"
                    :class="{ 's1-ai-chip--used': guidedForm.channels.includes(c) }"
                    type="button"
                    @click="acceptChannelSuggestion(c)"
                  >
                    <span>{{ c }}</span>
                    <svg v-if="!guidedForm.channels.includes(c)" width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M6 2v8M2 6h8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
                    <svg v-else width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M2 6l3 3 5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  </button>
                </div>
              </template>

              <!-- Section 4: Formats -->
              <template v-if="guidedSection === 4 && aiSuggestions.formats">
                <div class="s1-ai-category__row">
                  <p class="s1-ai-category__label">Suggested formats</p>
                  <button class="s1-ai-accept-all" type="button" @click="acceptAllFormats">Accept all</button>
                </div>
                <div class="s1-ai-chips">
                  <button
                    v-for="f in aiSuggestions.formats"
                    :key="f"
                    class="s1-ai-chip"
                    :class="{ 's1-ai-chip--used': guidedForm.formats.includes(f) }"
                    type="button"
                    @click="acceptFormatSuggestion(f)"
                  >
                    <span>{{ f }}</span>
                    <svg v-if="!guidedForm.formats.includes(f)" width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M6 2v8M2 6h8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
                    <svg v-else width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M2 6l3 3 5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  </button>
                </div>
              </template>

              <!-- Sections 5+: nothing context-specific to suggest -->
              <p v-if="guidedSection >= 5" class="s1-ai-hint">
                Suggestions were applied to sections 1–4. Review your entries before building.
              </p>
            </template>
          </div>

          <!-- Section completeness checklist -->
          <div class="s1-section-checklist">
            <p class="s1-section-checklist__title">Sections</p>
            <ul>
              <li v-for="(sec, i) in guidedSections" :key="i" class="s1-checklist-item" :class="{ 's1-checklist-item--done': isSectionDone(i), 's1-checklist-item--active': guidedSection === i }">
                <span class="s1-checklist-item__icon" aria-hidden="true">
                  <svg v-if="isSectionDone(i)" width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M1.5 5L4 7.5L8.5 2.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  <span v-else class="s1-checklist-item__dot"></span>
                </span>
                <span>{{ sec.label }}</span>
              </li>
            </ul>
          </div>
        </aside>
      </div>
    </template>

    <!-- ── Upload phases (idle + selected + resuming) ──────────────────── -->
    <template v-else-if="phase === 'idle' || phase === 'selected' || phase === 'resuming'">
      <div class="s1-upload-layout">

        <!-- Primary: upload zone -->
        <div class="s1-upload-primary">
          <div class="s1-section-header">
            <div class="s1-section-header__row">
              <div>
                <p class="eyebrow">Step 1 · Brand Intelligence</p>
                <h1 class="s1-section-header__title">
                  {{ phase === 'resuming' ? 'Brief uploaded — ready to analyze' : 'Upload your campaign brief' }}
                </h1>
                <p class="s1-section-header__lead">
                  {{ phase === 'resuming'
                    ? 'Your document is already uploaded. Build the intelligence map to continue to personas.'
                    : 'Upload your campaign document and our AI extracts products, target audiences, competitive signals, and marketing channels into a structured map.' }}
                </p>
              </div>
              <button v-if="phase === 'idle'" class="s1-back-link" @click="inputMethod = null">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M9 11L5 7l4-4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
                Back
              </button>
            </div>
          </div>

          <!-- Idle: drop zone -->
          <label
            v-if="phase === 'idle'"
            class="s1-dropzone"
            :class="{ 's1-dropzone--drag': dragging }"
            @dragover.prevent="dragging = true"
            @dragleave.prevent="dragging = false"
            @drop.prevent="onDrop"
          >
            <input type="file" accept=".pdf,.txt,application/pdf,text/plain" @change="onFileChange" />
            <div class="s1-dropzone__ring" aria-hidden="true">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
            </div>
            <p class="s1-dropzone__heading">Drop your campaign brief here</p>
            <p class="s1-dropzone__sub">or click to browse files</p>
            <div class="s1-dropzone__formats">
              <span>PDF</span>
              <span>TXT</span>
              <span>up to 10 MB</span>
            </div>
          </label>

          <!-- Selected: file confirmed -->
          <div v-else-if="phase === 'selected'" class="s1-file-confirmed">
            <div class="s1-file-confirmed__row">
              <div class="s1-file-confirmed__icon" aria-hidden="true">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
              </div>
              <div class="s1-file-confirmed__meta">
                <strong>{{ selectedFile.name }}</strong>
                <span>{{ readableSize(selectedFile.size) }} · Ready to analyze</span>
              </div>
              <button class="s1-file-confirmed__change" @click="clearFile">Change</button>
            </div>
            <AppButton size="lg" block @click="run">
              Analyze brief
            </AppButton>
            <p class="s1-upload-hint">AI extracts brand entities and maps relationships — takes 30–60 seconds.</p>
          </div>

          <!-- Resuming: already uploaded -->
          <div v-else class="s1-file-confirmed">
            <div class="s1-file-confirmed__row s1-file-confirmed__row--done">
              <div class="s1-file-confirmed__icon s1-file-confirmed__icon--done" aria-hidden="true">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
              </div>
              <div class="s1-file-confirmed__meta">
                <strong>{{ store.uploadedFile?.filename || "Campaign brief" }}</strong>
                <span class="s1-tag s1-tag--success">
                  <span class="s1-tag__dot" aria-hidden="true"></span>
                  Uploaded
                </span>
              </div>
            </div>
            <AppButton size="lg" block :loading="store.graph.loading" @click="prepare">
              Build intelligence map
            </AppButton>
          </div>

          <ErrorState v-if="store.graph.error" :message="store.graph.error" />
        </div>

        <!-- Secondary: What we'll extract -->
        <aside class="s1-upload-secondary">
          <div class="s1-preview-card">
            <p class="s1-preview-card__title">What we'll extract from your brief</p>
            <ul class="s1-entity-preview">
              <li v-for="cat in entityCategories" :key="cat.type">
                <span class="s1-entity-preview__icon" :style="{ background: cat.bgColor, color: cat.fgColor }" aria-hidden="true">
                  <component :is="cat.iconComponent" />
                </span>
                <div class="s1-entity-preview__text">
                  <strong>{{ cat.label }}</strong>
                  <p>{{ cat.description }}</p>
                </div>
              </li>
            </ul>
          </div>

          <div class="s1-how-it-works">
            <p class="s1-how-it-works__label">How it works</p>
            <ol class="s1-hiw-steps">
              <li>
                <span class="s1-hiw-steps__num">1</span>
                <div>
                  <strong>Upload</strong>
                  <p>Your PDF or text brief is securely processed by our AI.</p>
                </div>
              </li>
              <li>
                <span class="s1-hiw-steps__num">2</span>
                <div>
                  <strong>Extract</strong>
                  <p>AI identifies products, audiences, channels, and brand values.</p>
                </div>
              </li>
              <li>
                <span class="s1-hiw-steps__num">3</span>
                <div>
                  <strong>Map</strong>
                  <p>Entities are connected into a structured intelligence graph for simulation.</p>
                </div>
              </li>
            </ol>
          </div>
        </aside>
      </div>
    </template>

    <!-- ── Building phase ──────────────────────────────────────────────── -->
    <template v-else-if="phase === 'building'">
      <div class="s1-building-layout">

        <!-- Left: file + log -->
        <div class="s1-building-primary">
          <div class="s1-section-header">
            <p class="eyebrow">Step 1 · Analyzing</p>
            <h1 class="s1-section-header__title">Building your intelligence map</h1>
            <p class="s1-section-header__lead">Our AI is reading your brief and structuring your brand's world.</p>
          </div>

          <div class="s1-building-file-row">
            <div class="s1-building-file-row__icon" aria-hidden="true">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
            </div>
            <span class="s1-building-file-row__name">{{ selectedFile?.name || store.uploadedFile?.filename || "Campaign brief" }}</span>
            <span class="s1-tag s1-tag--processing">
              <span class="s1-tag__spinner" aria-hidden="true"></span>
              Analyzing
            </span>
          </div>

          <div class="s1-progress-wrap">
            <div class="s1-progress-track">
              <span class="s1-progress-fill" :style="{ width: `${store.graph.progress || 8}%` }"></span>
            </div>
            <span class="s1-progress-pct">{{ store.graph.progress || 8 }}%</span>
          </div>

          <div class="s1-extraction-log" aria-live="polite" aria-label="Extraction progress">
            <div
              v-for="(entry, i) in extractionLog"
              :key="i"
              class="s1-log-entry"
              :class="{
                's1-log-entry--done': entry.state === 'done',
                's1-log-entry--active': entry.state === 'active',
                's1-log-entry--pending': entry.state === 'pending',
              }"
            >
              <span class="s1-log-entry__icon" aria-hidden="true">
                <svg v-if="entry.state === 'done'" width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M2 6L5 9L10 3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span v-else-if="entry.state === 'active'" class="s1-log-spinner"></span>
                <span v-else class="s1-log-dot"></span>
              </span>
              <span class="s1-log-entry__text">{{ entry.message }}</span>
              <span v-if="entry.tag" class="s1-log-entry__tag">{{ entry.tag }}</span>
            </div>
          </div>
        </div>

        <!-- Right: entity categories scanning -->
        <aside class="s1-building-secondary">
          <p class="s1-building-secondary__title">Scanning for entity types</p>
          <ul class="s1-scanning-list">
            <li
              v-for="(cat, i) in entityCategories"
              :key="cat.type"
              class="s1-scanning-item"
              :class="{
                's1-scanning-item--found': logStep > i * 1.5,
                's1-scanning-item--scanning': logStep > i * 1.5 - 1 && logStep <= i * 1.5,
              }"
            >
              <span class="s1-scanning-item__icon" :style="{ background: cat.bgColor, color: cat.fgColor }" aria-hidden="true">
                <component :is="cat.iconComponent" />
              </span>
              <div class="s1-scanning-item__text">
                <strong>{{ cat.label }}</strong>
                <span v-if="logStep > i * 1.5" class="s1-scanning-item__found">Found</span>
                <span v-else-if="logStep > i * 1.5 - 1" class="s1-scanning-item__scanning">Scanning...</span>
                <span v-else class="s1-scanning-item__waiting">Waiting</span>
              </div>
              <span v-if="logStep > i * 1.5" class="s1-scanning-item__check" aria-hidden="true">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <circle cx="7" cy="7" r="6.5" fill="rgba(0,201,122,0.12)" stroke="rgba(0,201,122,0.4)"/>
                  <path d="M4 7L6.5 9.5L10 5" stroke="#00C97A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </span>
            </li>
          </ul>

          <div class="s1-building-secondary__footnote">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
              <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
            </svg>
            Real entity counts depend on your document's content.
          </div>
        </aside>
      </div>
    </template>

    <!-- ── Ready phase ─────────────────────────────────────────────────── -->
    <template v-else-if="phase === 'ready'">

      <!-- Stat cards -->
      <div class="s1-stat-row">
        <div class="s1-stat-card">
          <strong>{{ store.graph.nodes.length }}</strong>
          <span>Total entities</span>
        </div>
        <div class="s1-stat-card">
          <strong>{{ store.graph.edges.length }}</strong>
          <span>Relationships</span>
        </div>
        <div class="s1-stat-card s1-stat-card--accent">
          <strong>{{ audienceCount }}</strong>
          <span>Audience segments</span>
        </div>
        <div class="s1-stat-card">
          <strong>{{ channelCount }}</strong>
          <span>Channels mapped</span>
        </div>
      </div>

      <!-- Success banner + CTA -->
      <div class="s1-success-banner" role="status">
        <span class="s1-success-banner__pulse" aria-hidden="true"></span>
        <p class="s1-success-banner__text">
          Intelligence map complete —
          <strong>{{ store.graph.nodes.length }} entities</strong> extracted from
          {{ store.uploadedFile?.filename ? `"${store.uploadedFile.filename}"` : 'your brief' }}.
          Ready to generate your audience.
        </p>
        <AppButton size="sm" @click="store.goToStep(2)">Continue to Personas →</AppButton>
      </div>

      <!-- Full-width graph with floating entity overlay -->
      <div class="s1-graph-wrap">
        <!-- Graph canvas -->
        <div class="s1-graph-panel">
          <div class="s1-graph-panel__canvas">
            <GraphPanel
              :nodes="store.graph.nodes"
              :edges="store.graph.edges"
              :showHeader="false"
              @select-node="selectedNode = $event"
            />
          </div>
        </div>

        <!-- Floating entities toggle button -->
        <button
          class="s1-entities-toggle"
          :class="{ 's1-entities-toggle--active': showEntities }"
          @click="showEntities = !showEntities"
          :title="showEntities ? 'Hide entities' : 'Show extracted entities'"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="8" cy="18" r="4"/><path d="M12 18V2l7 4"/>
          </svg>
          <span>Entities</span>
          <span class="s1-entities-toggle__count">{{ store.graph.nodes.length }}</span>
          <svg class="s1-entities-toggle__chevron" :class="{ flipped: showEntities }" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </button>

        <!-- Floating entities drawer overlay -->
        <Transition name="s1-drawer">
          <aside v-if="showEntities" class="s1-breakdown-panel">
            <div class="s1-breakdown-panel__head">
              <p class="s1-breakdown-panel__title">Extracted entities</p>
              <p class="s1-breakdown-panel__sub">{{ store.graph.nodes.length }} entities · {{ categorizedNodes.filter(c => c.nodes.length).length }} categories</p>
              <button class="s1-breakdown-close" @click="showEntities = false" title="Close">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>

            <div class="s1-breakdown-scroll">
              <div v-for="cat in categorizedNodes" :key="cat.type" class="s1-breakdown-section">
                <div class="s1-breakdown-section__head">
                  <span class="s1-breakdown-section__icon" :style="{ background: cat.bgColor, color: cat.fgColor }" aria-hidden="true">
                    <component :is="cat.iconComponent" />
                  </span>
                  <strong class="s1-breakdown-section__label">{{ cat.label }}</strong>
                  <span class="s1-breakdown-section__count">{{ cat.nodes.length }}</span>
                </div>
                <ul class="s1-breakdown-section__nodes">
                  <li
                    v-for="node in cat.nodes"
                    :key="node.id || node.uuid"
                    class="s1-breakdown-node"
                    :class="{ 's1-breakdown-node--selected': selectedNode?.id === node.id }"
                    @click="selectedNode = node"
                  >
                    {{ node.label || node.name }}
                  </li>
                </ul>
              </div>
            </div>

            <div class="s1-breakdown-panel__footer">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
              <span>{{ store.uploadedFile?.filename || "Campaign brief" }}</span>
            </div>
          </aside>
        </Transition>
      </div>
    </template>

    <!-- Node detail drawer -->
    <DrawerPanel
      :open="Boolean(selectedNode)"
      :title="selectedNode?.label || 'Entity'"
      :eyebrow="selectedNode?.type"
      @close="selectedNode = null"
    >
      <template v-if="selectedNode">
        <div class="s1-node-type-chip">
          <span
            :style="{
              background: entityCategories.find(c => c.type === selectedNode.type)?.bgColor || 'rgba(255,255,255,0.06)',
              color: entityCategories.find(c => c.type === selectedNode.type)?.fgColor || 'var(--color-text-muted)',
            }"
          >{{ selectedNode.type }}</span>
        </div>
        <dl class="s1-node-dl" v-if="selectedNode.attributes && Object.keys(selectedNode.attributes).length">
          <div v-for="(value, key) in selectedNode.attributes" :key="key">
            <dt>{{ key }}</dt>
            <dd>{{ Array.isArray(value) ? value.join(", ") : value }}</dd>
          </div>
        </dl>
        <p v-else class="s1-node-empty">No additional attributes for this entity.</p>
      </template>
    </DrawerPanel>

  </div>
</template>

<script setup>
import { computed, h, onUnmounted, reactive, ref, watch } from "vue";
import AppButton from "@/components/common/AppButton.vue";
import DrawerPanel from "@/components/common/DrawerPanel.vue";
import ErrorState from "@/components/common/ErrorState.vue";
import GraphPanel from "@/components/graph/GraphPanel.vue";
import { useCampaignStore } from "@/stores/campaignStore";
import { suggestBrandIntel } from "@/api/campaignApi";

const store = useCampaignStore();
const selectedFile = ref(null);
const selectedNode = ref(null);
const showEntities = ref(false);
const dragging = ref(false);
const inputMethod = ref(null); // null | 'guided' | 'upload'

// ── Guided form state ──────────────────────────────────────────────────────
const guidedSection = ref(0);
const guidedForm = reactive({
  brandName: "",
  industry: "",
  valueProposition: "",
  brandValues: "",
  products: [{ name: "", description: "" }],
  audiences: [{ name: "", ageRange: "", description: "" }],
  channels: [],
  formats: [],
  objective: "",
});

const INDUSTRIES = [
  "Consumer Goods", "Retail & E-Commerce", "Software & SaaS", "Financial Services",
  "Healthcare & Wellness", "Media & Entertainment", "Travel & Hospitality",
  "Automotive", "Education & EdTech", "Food & Beverage", "Real Estate",
  "Professional Services", "Non-Profit", "Other",
];

const CHANNELS = [
  "Instagram", "Facebook", "LinkedIn", "Twitter / X", "TikTok", "YouTube",
  "Email Marketing", "Google Search", "Display Ads", "Podcast Advertising",
  "SMS / Push Notifications", "Influencer Marketing", "TV / Radio", "Out-of-Home",
];

const FORMATS = [
  "Video Ads", "Image Ads", "Story Ads", "Reels / Shorts", "Blog Posts",
  "Email Newsletter", "Infographic", "Interactive Quiz", "Webinar",
  "Podcast Episode", "Case Study", "Whitepaper", "UGC", "Live Stream",
];

const OBJECTIVES = [
  { value: "awareness", label: "Brand Awareness", desc: "Reach new audiences and grow brand recognition at scale." },
  { value: "leads", label: "Lead Generation", desc: "Capture qualified leads through targeted, high-intent campaigns." },
  { value: "conversion", label: "Sales Conversion", desc: "Drive purchases and direct revenue from campaign activity." },
  { value: "retention", label: "Customer Retention", desc: "Re-engage existing customers and reduce churn rate." },
  { value: "launch", label: "Product Launch", desc: "Build anticipation and drive adoption for a new offering." },
  { value: "education", label: "Market Education", desc: "Inform your audience about a new category or concept." },
];

const guidedSections = [
  { label: "Brand Identity" },
  { label: "Products & Services" },
  { label: "Target Audience" },
  { label: "Marketing Channels" },
  { label: "Content Formats" },
  { label: "Campaign Objective" },
];

function isSectionDone(i) {
  if (i === 0) return !!(guidedForm.brandName && guidedForm.industry && guidedForm.valueProposition);
  if (i === 1) return guidedForm.products.some((p) => p.name.trim());
  if (i === 2) return guidedForm.audiences.some((a) => a.name.trim());
  if (i === 3) return guidedForm.channels.length > 0;
  if (i === 4) return guidedForm.formats.length > 0;
  if (i === 5) return !!guidedForm.objective;
  return false;
}

const guidedIsComplete = computed(() => guidedSections.every((_, i) => isSectionDone(i)));

const guidedCompletionPercent = computed(() => {
  const done = guidedSections.filter((_, i) => isSectionDone(i)).length;
  return Math.round((done / guidedSections.length) * 100);
});

// Live intelligence preview
const guidedPreview = computed(() => {
  const items = [];
  if (guidedForm.brandName) items.push({ type: "Brand", label: guidedForm.brandName });
  guidedForm.products.filter((p) => p.name.trim()).forEach((p) => items.push({ type: "Product", label: p.name }));
  guidedForm.audiences.filter((a) => a.name.trim()).forEach((a) => items.push({ type: "CustomerPersona", label: a.name }));
  guidedForm.channels.forEach((c) => items.push({ type: "MarketingChannel", label: c }));
  guidedForm.formats.forEach((f) => items.push({ type: "ContentFormat", label: f }));
  return items;
});

const guidedPreviewGrouped = computed(() => {
  return entityCategories
    .map((cat) => ({
      ...cat,
      items: guidedPreview.value.filter((p) => p.type === cat.type).map((p) => p.label),
    }))
    .filter((cat) => cat.items.length > 0);
});

function addProduct() {
  guidedForm.products.push({ name: "", description: "" });
}
function removeProduct(i) {
  if (guidedForm.products.length > 1) guidedForm.products.splice(i, 1);
}
function addAudience() {
  if (guidedForm.audiences.length < 3) guidedForm.audiences.push({ name: "", ageRange: "", description: "" });
}
function removeAudience(i) {
  if (guidedForm.audiences.length > 1) guidedForm.audiences.splice(i, 1);
}
function toggleChip(arr, value) {
  const idx = arr.indexOf(value);
  if (idx >= 0) arr.splice(idx, 1);
  else arr.push(value);
}

// ── AI Suggestions ─────────────────────────────────────────────────────────
const aiSuggestions = ref(null); // null | 'loading' | { products, audiences, channels, formats }
const aiSuggestionsKey = ref("");

const section0Complete = computed(() => isSectionDone(0));

watch(
  [section0Complete, () => guidedForm.brandName, () => guidedForm.industry],
  ([complete, name, industry]) => {
    if (!complete) {
      aiSuggestions.value = null;
      aiSuggestionsKey.value = "";
      return;
    }
    const key = `${name.trim()}::${industry}`;
    if (aiSuggestionsKey.value === key) return;
    fetchAiSuggestions(key);
  },
);

async function fetchAiSuggestions(key) {
  aiSuggestionsKey.value = key;
  aiSuggestions.value = "loading";
  try {
    const result = await suggestBrandIntel({
      brandName: guidedForm.brandName,
      industry: guidedForm.industry,
      valueProposition: guidedForm.valueProposition,
    });
    if (aiSuggestionsKey.value === key) {
      aiSuggestions.value = result.suggestions;
    }
  } catch {
    if (aiSuggestionsKey.value === key) {
      aiSuggestions.value = null;
    }
  }
}

function isProductAccepted(name) {
  return guidedForm.products.some((p) => p.name.toLowerCase() === name.toLowerCase());
}

function isAudienceAccepted(name) {
  return guidedForm.audiences.some((a) => a.name.toLowerCase() === name.toLowerCase());
}

function acceptProductSuggestion(product) {
  if (isProductAccepted(product.name)) return;
  const emptyIdx = guidedForm.products.findIndex((p) => !p.name.trim());
  if (emptyIdx >= 0) {
    guidedForm.products[emptyIdx].name = product.name;
    guidedForm.products[emptyIdx].description = product.description || "";
  } else if (guidedForm.products.length < 8) {
    guidedForm.products.push({ name: product.name, description: product.description || "" });
  }
}

function acceptAudienceSuggestion(audience) {
  if (isAudienceAccepted(audience.name)) return;
  const emptyIdx = guidedForm.audiences.findIndex((a) => !a.name.trim());
  if (emptyIdx >= 0) {
    guidedForm.audiences[emptyIdx].name = audience.name;
    guidedForm.audiences[emptyIdx].ageRange = audience.ageRange || "";
    guidedForm.audiences[emptyIdx].description = audience.description || "";
  } else if (guidedForm.audiences.length < 3) {
    guidedForm.audiences.push({ name: audience.name, ageRange: audience.ageRange || "", description: audience.description || "" });
  }
}

function acceptChannelSuggestion(channel) {
  if (!guidedForm.channels.includes(channel)) guidedForm.channels.push(channel);
}

function acceptFormatSuggestion(format) {
  if (!guidedForm.formats.includes(format)) guidedForm.formats.push(format);
}

function acceptAllChannels() {
  if (typeof aiSuggestions.value === "object" && aiSuggestions.value?.channels) {
    aiSuggestions.value.channels.forEach((c) => acceptChannelSuggestion(c));
  }
}

function acceptAllFormats() {
  if (typeof aiSuggestions.value === "object" && aiSuggestions.value?.formats) {
    aiSuggestions.value.formats.forEach((f) => acceptFormatSuggestion(f));
  }
}

function guidedFormToText() {
  const products = guidedForm.products
    .filter((p) => p.name.trim())
    .map((p) => (p.description ? `${p.name}: ${p.description}` : p.name))
    .join("; ");
  const audiences = guidedForm.audiences
    .filter((a) => a.name.trim())
    .map((a) => [a.name, a.ageRange && `Age ${a.ageRange}`, a.description].filter(Boolean).join(", "))
    .join("; ");
  const obj = OBJECTIVES.find((o) => o.value === guidedForm.objective);
  const lines = [
    `Brand Name: ${guidedForm.brandName}`,
    `Industry: ${guidedForm.industry}`,
    `Value Proposition: ${guidedForm.valueProposition}`,
  ];
  if (guidedForm.brandValues.trim()) lines.push(`Brand Values: ${guidedForm.brandValues}`);
  if (products) lines.push(`Products & Services: ${products}`);
  if (audiences) lines.push(`Target Audiences: ${audiences}`);
  if (guidedForm.channels.length) lines.push(`Marketing Channels: ${guidedForm.channels.join(", ")}`);
  if (guidedForm.formats.length) lines.push(`Content Formats: ${guidedForm.formats.join(", ")}`);
  if (obj) lines.push(`Campaign Objective: ${obj.label}`);
  return lines.join("\n");
}

async function runGuided() {
  store.graph.error = null;
  try {
    const text = guidedFormToText();
    const file = new File([text], "brand-brief.txt", { type: "text/plain" });
    const obj = OBJECTIVES.find((o) => o.value === guidedForm.objective);
    const simulationRequirement = obj
      ? `Campaign objective: ${obj.label}. Brand: ${guidedForm.brandName}. Industry: ${guidedForm.industry}. Extract brand intelligence: products, audiences, channels, and competitive landscape.`
      : `Extract brand intelligence for ${guidedForm.brandName}: products, audiences, channels, and competitive landscape.`;
    await store.uploadBrandBrief(file, simulationRequirement);
    await store.prepareGraph();
  } catch (error) {
    store.graph.error = error?.message || "Something went wrong. Please try again.";
  }
}

// ── Extraction log simulation ──────────────────────────────────────────────
const logStep = ref(0);
let logTimer = null;

const extractionLog = [
  { message: "Reading document structure", tag: null },
  { message: "Identifying brand entities", tag: "Brand" },
  { message: "Extracting product offerings", tag: "Products" },
  { message: "Mapping target audience segments", tag: "Audiences" },
  { message: "Discovering marketing channels", tag: "Channels" },
  { message: "Analyzing content formats", tag: "Formats" },
  { message: "Building relationship connections", tag: null },
  { message: "Finalizing intelligence graph", tag: null },
].map((entry, i) => ({
  ...entry,
  get state() {
    if (logStep.value > i) return "done";
    if (logStep.value === i) return "active";
    return "pending";
  },
}));

function startExtractionLog() {
  logStep.value = 0;
  logTimer = setInterval(() => {
    if (logStep.value < extractionLog.length - 1) {
      logStep.value++;
    } else {
      clearInterval(logTimer);
    }
  }, 1800);
}

function stopExtractionLog() {
  if (logTimer) {
    clearInterval(logTimer);
    logTimer = null;
  }
}

// ── Phase computation ──────────────────────────────────────────────────────
const phase = computed(() => {
  if (store.graphReady) return "ready";
  if (store.graph.loading) return "building";
  if (store.graphId && !store.graph.nodes.length) return "resuming";
  if (inputMethod.value === "guided") return "guided";
  if (inputMethod.value === "upload") return selectedFile.value ? "selected" : "idle";
  return "entry";
});

watch(phase, (val, prev) => {
  if (val === "building" && prev !== "building") {
    startExtractionLog();
  } else if (val !== "building") {
    stopExtractionLog();
    if (val === "ready") logStep.value = extractionLog.length;
  }
});

onUnmounted(stopExtractionLog);

// ── Entity category metadata ───────────────────────────────────────────────
const IconBrand = () =>
  h("svg", { width: 14, height: 14, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.6", "stroke-linecap": "round", "stroke-linejoin": "round" }, [
    h("path", { d: "M12 2L2 7l10 5 10-5-10-5z" }),
    h("path", { d: "M2 17l10 5 10-5" }),
    h("path", { d: "M2 12l10 5 10-5" }),
  ]);

const IconProduct = () =>
  h("svg", { width: 14, height: 14, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.6", "stroke-linecap": "round", "stroke-linejoin": "round" }, [
    h("path", { d: "M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" }),
  ]);

const IconPersona = () =>
  h("svg", { width: 14, height: 14, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.6", "stroke-linecap": "round", "stroke-linejoin": "round" }, [
    h("path", { d: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" }),
    h("circle", { cx: "9", cy: "7", r: "4" }),
    h("path", { d: "M23 21v-2a4 4 0 0 0-3-3.87" }),
    h("path", { d: "M16 3.13a4 4 0 0 1 0 7.75" }),
  ]);

const IconChannel = () =>
  h("svg", { width: 14, height: 14, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.6", "stroke-linecap": "round", "stroke-linejoin": "round" }, [
    h("path", { d: "M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z" }),
  ]);

const IconFormat = () =>
  h("svg", { width: 14, height: 14, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.6", "stroke-linecap": "round", "stroke-linejoin": "round" }, [
    h("rect", { x: "3", y: "3", width: "18", height: "18", rx: "2", ry: "2" }),
    h("path", { d: "M3 9h18M9 21V9" }),
  ]);

const entityCategories = [
  { type: "Brand", label: "Brand Identity", description: "Core brand, values, and positioning signals", bgColor: "rgba(10,191,173,0.12)", fgColor: "var(--color-accent)", iconComponent: IconBrand },
  { type: "Product", label: "Products & Offerings", description: "Products, services, and features mentioned", bgColor: "rgba(99,102,241,0.12)", fgColor: "#818cf8", iconComponent: IconProduct },
  { type: "CustomerPersona", label: "Audience Segments", description: "Target demographics and customer personas", bgColor: "rgba(0,201,122,0.12)", fgColor: "var(--color-accent-2)", iconComponent: IconPersona },
  { type: "MarketingChannel", label: "Marketing Channels", description: "Distribution and media channels", bgColor: "rgba(240,165,0,0.12)", fgColor: "#f0a500", iconComponent: IconChannel },
  { type: "ContentFormat", label: "Content Formats", description: "Ad formats, creative types, and media", bgColor: "rgba(236,72,153,0.12)", fgColor: "#f472b6", iconComponent: IconFormat },
];

// ── Computed metrics ───────────────────────────────────────────────────────
const audienceCount = computed(() => store.graph.nodes.filter((n) => n.type === "CustomerPersona").length);
const channelCount = computed(() => store.graph.nodes.filter((n) => n.type === "MarketingChannel").length);
const categorizedNodes = computed(() =>
  entityCategories
    .map((cat) => ({ ...cat, nodes: store.graph.nodes.filter((n) => n.type === cat.type) }))
    .filter((cat) => cat.nodes.length > 0)
);

// ── File handling ──────────────────────────────────────────────────────────
function onFileChange(event) {
  selectedFile.value = event.target.files?.[0] || null;
}
function onDrop(event) {
  dragging.value = false;
  const file = event.dataTransfer?.files?.[0];
  if (file) selectedFile.value = file;
}
function clearFile() {
  selectedFile.value = null;
  store.graph.error = null;
}
function readableSize(bytes = 0) {
  if (!bytes) return "";
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

async function run() {
  store.graph.error = null;
  try {
    const simulationRequirement =
      "Extract brand intelligence: products, audiences, channels, content formats, and competitive landscape.";
    await store.uploadBrandBrief(selectedFile.value, simulationRequirement);
    await store.prepareGraph();
  } catch (error) {
    store.graph.error = error?.message || "Something went wrong. Please try again.";
  }
}

async function prepare() {
  store.graph.error = null;
  try {
    await store.prepareGraph();
  } catch (error) {
    store.graph.error = error?.message || "Graph build failed.";
  }
}
</script>

<style scoped>
/* ── Root ─────────────────────────────────────────────────────────────────── */
.s1-root {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* ── Section header ───────────────────────────────────────────────────────── */
.s1-section-header {
  margin-bottom: 0.25rem;
}
.s1-section-header .eyebrow {
  margin-bottom: 0.45rem;
}
.s1-section-header__title {
  font-size: clamp(1.35rem, 3vw, 1.75rem);
  font-family: var(--font-display);
  font-weight: 800;
  letter-spacing: -0.025em;
  line-height: 1.2;
  margin: 0 0 0.65rem;
  color: var(--color-text);
}
.s1-section-header__lead {
  font-size: 0.9rem;
  color: var(--color-text-muted);
  line-height: 1.65;
  margin: 0;
  max-width: 48ch;
}
.s1-section-header__row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

/* Back link */
.s1-back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-subtle);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0.35rem 0.65rem;
  white-space: nowrap;
  flex-shrink: 0;
  margin-top: 0.2rem;
  transition: color var(--transition-fast), border-color var(--transition-fast);
}
.s1-back-link:hover {
  color: var(--color-text-muted);
  border-color: var(--color-border-strong);
}

/* ── Entry layout ──────────────────────────────────────────────────────────── */
.s1-entry-layout {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.s1-entry-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  align-items: stretch;
}

.s1-entry-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.5rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-bg-elevated);
  text-align: left;
  cursor: pointer;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast), background var(--transition-fast);
  min-height: 280px;
}
.s1-entry-card:not(.s1-entry-card--disabled):hover {
  border-color: var(--color-border-strong);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.12);
}
.s1-entry-card--primary {
  border-color: rgba(10, 191, 173, 0.3);
  background: linear-gradient(135deg, rgba(10, 191, 173, 0.04) 0%, var(--color-bg-elevated) 60%);
}
.s1-entry-card--primary:hover {
  border-color: var(--color-accent);
  box-shadow: 0 4px 32px rgba(10, 191, 173, 0.12);
}
.s1-entry-card--disabled {
  cursor: default;
  opacity: 0.5;
}

.s1-entry-card__badge {
  position: absolute;
  top: -0.6rem;
  left: 1.25rem;
  font-size: 0.66rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-accent);
  background: var(--color-bg-base);
  border: 1px solid rgba(10, 191, 173, 0.35);
  border-radius: var(--radius-full);
  padding: 0.15rem 0.55rem;
}
.s1-entry-card__badge--muted {
  color: var(--color-text-ghost);
  border-color: var(--color-border);
}

.s1-entry-card__icon {
  display: grid;
  place-items: center;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.s1-entry-card__title {
  font-size: 1rem;
  font-family: var(--font-display);
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.s1-entry-card__desc {
  font-size: 0.84rem;
  color: var(--color-text-muted);
  line-height: 1.55;
  margin: 0;
  flex: 1;
}

.s1-entry-card__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.s1-entry-card__list li {
  font-size: 0.78rem;
  color: var(--color-text-subtle);
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.s1-entry-card__list li::before {
  content: "";
  display: inline-block;
  width: 0.3rem;
  height: 0.3rem;
  border-radius: 50%;
  background: var(--color-border-strong);
  flex-shrink: 0;
}

.s1-entry-card__cta {
  font-size: 0.84rem;
  font-weight: 700;
  color: var(--color-accent);
  display: flex;
  align-items: center;
  gap: 0.3rem;
  margin-top: auto;
  padding-top: 0.25rem;
}

/* ── Guided layout ─────────────────────────────────────────────────────────── */
.s1-guided-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 2rem;
  align-items: start;
}

.s1-guided-primary {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  min-width: 0;
}

/* Stepper */
.s1-stepper {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
}
.s1-stepper__item {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  padding: 0.3rem 0.7rem 0.3rem 0.45rem;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--color-text-ghost);
  transition: border-color var(--transition-fast), color var(--transition-fast), background var(--transition-fast);
}
.s1-stepper__item:hover {
  border-color: var(--color-border-strong);
  color: var(--color-text-subtle);
}
.s1-stepper__item--active {
  border-color: var(--color-accent);
  color: var(--color-accent);
  background: rgba(10, 191, 173, 0.06);
}
.s1-stepper__item--done {
  border-color: rgba(0, 201, 122, 0.3);
  color: var(--color-accent-2);
  background: rgba(0, 201, 122, 0.05);
}
.s1-stepper__pip {
  display: grid;
  place-items: center;
  width: 1.2rem;
  height: 1.2rem;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid currentColor;
  font-size: 0.64rem;
  font-weight: 800;
  flex-shrink: 0;
}
.s1-stepper__item--done .s1-stepper__pip {
  background: rgba(0, 201, 122, 0.12);
}
.s1-stepper__label {
  white-space: nowrap;
}

/* Guided section */
.s1-guided-section {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-bg-elevated);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.s1-guided-section__title {
  font-size: 1rem;
  font-family: var(--font-display);
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}
.s1-guided-section__sub {
  font-size: 0.84rem;
  color: var(--color-text-muted);
  line-height: 1.55;
  margin: -0.75rem 0 0;
}

/* Form fields */
.s1-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}
.s1-form-field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.s1-form-field--full {
  grid-column: 1 / -1;
}
.s1-form-label {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--color-text-subtle);
  letter-spacing: 0.02em;
}
.s1-form-hint {
  font-weight: 400;
  color: var(--color-text-ghost);
}
.s1-required {
  color: var(--color-accent);
  font-weight: 700;
}
.s1-form-input {
  background: var(--color-bg-base);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text);
  font-size: 0.875rem;
  padding: 0.55rem 0.75rem;
  width: 100%;
  box-sizing: border-box;
  font-family: var(--font-body);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
  outline: none;
}
.s1-form-input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(10, 191, 173, 0.1);
}
.s1-form-input::placeholder {
  color: var(--color-text-ghost);
}
.s1-form-select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg width='10' height='6' viewBox='0 0 10 6' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1L5 5L9 1' stroke='%23666' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.75rem center;
  padding-right: 2rem;
}
.s1-form-textarea {
  background: var(--color-bg-base);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text);
  font-size: 0.875rem;
  padding: 0.55rem 0.75rem;
  width: 100%;
  box-sizing: border-box;
  font-family: var(--font-body);
  resize: vertical;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
  outline: none;
  line-height: 1.55;
}
.s1-form-textarea:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(10, 191, 173, 0.1);
}
.s1-form-textarea::placeholder {
  color: var(--color-text-ghost);
}

/* Product list */
.s1-product-list {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}
.s1-product-row {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}
.s1-product-row__fields {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.65rem;
  min-width: 0;
}
.s1-product-row__remove {
  display: grid;
  place-items: center;
  width: 1.75rem;
  height: 1.75rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: none;
  color: var(--color-text-ghost);
  cursor: pointer;
  flex-shrink: 0;
  transition: color var(--transition-fast), border-color var(--transition-fast);
}
.s1-product-row__remove:hover {
  color: #f472b6;
  border-color: rgba(244, 114, 182, 0.4);
}
.s1-add-row {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: none;
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-ghost);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0.45rem 0.85rem;
  transition: color var(--transition-fast), border-color var(--transition-fast);
  align-self: flex-start;
}
.s1-add-row:hover {
  color: var(--color-accent);
  border-color: rgba(10, 191, 173, 0.4);
}

/* Audience cards */
.s1-audience-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.s1-audience-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 1rem;
  background: var(--color-bg-base);
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}
.s1-audience-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.s1-audience-card__num {
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--color-text-ghost);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

/* Chips */
.s1-chip-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.s1-chip {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  color: var(--color-text-subtle);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0.35rem 0.85rem;
  transition: border-color var(--transition-fast), color var(--transition-fast), background var(--transition-fast);
}
.s1-chip:hover {
  border-color: var(--color-border-strong);
  color: var(--color-text-muted);
}
.s1-chip--selected {
  background: rgba(10, 191, 173, 0.1);
  border-color: rgba(10, 191, 173, 0.4);
  color: var(--color-accent);
}

/* Objective grid */
.s1-objective-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.65rem;
}
.s1-objective-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  padding: 0.85rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-base);
  text-align: left;
  cursor: pointer;
  transition: border-color var(--transition-fast), background var(--transition-fast);
}
.s1-objective-card:hover {
  border-color: var(--color-border-strong);
}
.s1-objective-card--selected {
  border-color: var(--color-accent);
  background: rgba(10, 191, 173, 0.05);
}
.s1-objective-card strong {
  font-size: 0.875rem;
  font-family: var(--font-display);
  color: var(--color-text);
  font-weight: 700;
}
.s1-objective-card p {
  font-size: 0.75rem;
  color: var(--color-text-subtle);
  margin: 0;
  line-height: 1.5;
}
.s1-objective-card__check {
  position: absolute;
  top: 0.6rem;
  right: 0.6rem;
  display: grid;
  place-items: center;
  width: 1.2rem;
  height: 1.2rem;
  border-radius: 50%;
  background: rgba(10, 191, 173, 0.15);
  color: var(--color-accent);
  border: 1px solid rgba(10, 191, 173, 0.35);
}

/* Section nav */
.s1-section-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0.5rem;
  border-top: 1px solid var(--color-border);
  gap: 0.75rem;
}
.s1-section-nav--final {
  flex-wrap: wrap;
}
.s1-section-nav__back,
.s1-section-nav__next {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-subtle);
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0.45rem 0.85rem;
  transition: color var(--transition-fast), border-color var(--transition-fast);
}
.s1-section-nav__back:hover {
  color: var(--color-text-muted);
  border-color: var(--color-border-strong);
}
.s1-section-nav__next {
  border-color: rgba(10, 191, 173, 0.3);
  color: var(--color-accent);
  background: rgba(10, 191, 173, 0.05);
}
.s1-section-nav__next:hover:not(:disabled) {
  border-color: var(--color-accent);
  background: rgba(10, 191, 173, 0.1);
}
.s1-section-nav__next:disabled {
  opacity: 0.35;
  cursor: default;
}

/* ── Guided secondary: live preview ─────────────────────────────────────────── */
.s1-guided-secondary {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  position: sticky;
  top: calc(3.5rem + 1.5rem);
}

.s1-preview-live {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-bg-elevated);
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.s1-preview-live__title {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--color-text-subtle);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin: 0;
}
.s1-preview-live__sub {
  font-size: 0.74rem;
  color: var(--color-text-ghost);
  margin: -0.65rem 0 0;
}

.s1-preview-live__progress {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.s1-preview-live__entities {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.s1-preview-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.s1-preview-group__head {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}
.s1-preview-group__icon {
  display: grid;
  place-items: center;
  width: 1.4rem;
  height: 1.4rem;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}
.s1-preview-group__label {
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--color-text-muted);
  flex: 1;
}
.s1-preview-group__count {
  font-size: 0.68rem;
  font-weight: 700;
  font-family: var(--font-data);
  color: var(--color-text-ghost);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  padding: 0.05rem 0.35rem;
}
.s1-preview-group__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  padding-left: 1.85rem;
}
.s1-preview-tag {
  font-size: 0.72rem;
  font-weight: 600;
  border: 1px solid;
  border-radius: var(--radius-full);
  padding: 0.15rem 0.5rem;
  background: rgba(255, 255, 255, 0.02);
}

.s1-preview-live__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.65rem;
  padding: 1.5rem 0;
  color: var(--color-text-ghost);
  text-align: center;
}
.s1-preview-live__empty p {
  font-size: 0.78rem;
  margin: 0;
  line-height: 1.5;
  max-width: 22ch;
}

/* Section checklist */
.s1-section-checklist {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-bg-elevated);
  padding: 1rem 1.25rem;
}
.s1-section-checklist__title {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--color-text-ghost);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  margin: 0 0 0.75rem;
}
.s1-section-checklist ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}
.s1-checklist-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--color-text-ghost);
  transition: color var(--transition-fast);
}
.s1-checklist-item--active {
  color: var(--color-text-subtle);
  font-weight: 600;
}
.s1-checklist-item--done {
  color: var(--color-accent-2);
}
.s1-checklist-item__icon {
  display: grid;
  place-items: center;
  width: 1.1rem;
  height: 1.1rem;
  border-radius: 50%;
  flex-shrink: 0;
  border: 1px solid currentColor;
  opacity: 0.7;
}
.s1-checklist-item--done .s1-checklist-item__icon {
  background: rgba(0, 201, 122, 0.12);
  opacity: 1;
}
.s1-checklist-item__dot {
  display: block;
  width: 0.3rem;
  height: 0.3rem;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.5;
}

/* ── AI Suggestions panel ─────────────────────────────────────────────────── */
.s1-ai-suggestions {
  border: 1px solid var(--glass-border-glow);
  border-radius: var(--radius-md);
  padding: 0.85rem 1rem;
  background: linear-gradient(135deg, rgba(10,191,173,0.06) 0%, rgba(0,201,122,0.03) 100%);
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}
.s1-ai-suggestions--loading {
  opacity: 0.8;
}
.s1-ai-suggestions__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}
.s1-ai-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--color-accent);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.s1-ai-status {
  font-size: 0.72rem;
  color: var(--color-text-subtle);
}
.s1-ai-status--ready {
  color: var(--color-accent-2);
}
.s1-ai-hint {
  font-size: 0.78rem;
  color: var(--color-text-subtle);
  margin: 0;
  line-height: 1.5;
}
.s1-ai-category__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}
.s1-ai-category__label {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0;
}
.s1-ai-accept-all {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--color-accent);
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
  opacity: 0.85;
  transition: opacity var(--transition-fast);
}
.s1-ai-accept-all:hover {
  opacity: 1;
}
.s1-ai-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}
.s1-ai-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.3rem 0.6rem;
  font-size: 0.78rem;
  font-weight: 500;
  border-radius: var(--radius-full);
  border: 1px solid rgba(10, 191, 173, 0.35);
  background: rgba(10, 191, 173, 0.07);
  color: var(--color-text);
  cursor: pointer;
  transition:
    border-color var(--transition-fast),
    background var(--transition-fast),
    color var(--transition-fast);
}
.s1-ai-chip:hover:not(.s1-ai-chip--used) {
  border-color: var(--color-accent);
  background: rgba(10, 191, 173, 0.14);
  color: var(--color-accent);
}
.s1-ai-chip--used {
  border-color: rgba(0, 201, 122, 0.45);
  background: rgba(0, 201, 122, 0.1);
  color: var(--color-accent-2);
  cursor: default;
}
.s1-ai-shimmer {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  padding: 0.25rem 0;
}
.s1-ai-shimmer__bar {
  display: block;
  height: 0.7rem;
  border-radius: var(--radius-full);
  background: linear-gradient(90deg, rgba(10,191,173,0.1) 0%, rgba(10,191,173,0.22) 50%, rgba(10,191,173,0.1) 100%);
  background-size: 200% 100%;
  animation: ai-shimmer 1.4s ease-in-out infinite;
}
@keyframes ai-shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── Upload layout (two-column) ───────────────────────────────────────────── */
.s1-upload-layout {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 2rem;
  align-items: start;
}
.s1-upload-primary {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  min-width: 0;
}

/* Drop zone */
.s1-dropzone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.85rem;
  padding: 3.5rem 2rem;
  border: 1.5px dashed var(--color-border-strong);
  border-radius: var(--radius-lg);
  background: var(--color-bg-elevated);
  cursor: pointer;
  text-align: center;
  transition:
    border-color var(--transition-fast),
    background var(--transition-fast),
    box-shadow var(--transition-fast);
  position: relative;
}
.s1-dropzone input[type="file"] {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
  width: 100%;
  height: 100%;
}
.s1-dropzone:hover,
.s1-dropzone:focus-within,
.s1-dropzone--drag {
  border-color: var(--color-accent);
  background: rgba(10, 191, 173, 0.04);
  box-shadow: 0 0 0 3px rgba(10, 191, 173, 0.08), inset 0 0 24px rgba(10, 191, 173, 0.03);
}
.s1-dropzone__ring {
  display: grid;
  place-items: center;
  width: 4rem;
  height: 4rem;
  border-radius: 50%;
  border: 1.5px solid rgba(10, 191, 173, 0.25);
  background: rgba(10, 191, 173, 0.08);
  color: var(--color-accent);
  margin-bottom: 0.25rem;
  transition: box-shadow var(--transition-fast), background var(--transition-fast);
}
.s1-dropzone:hover .s1-dropzone__ring,
.s1-dropzone--drag .s1-dropzone__ring {
  background: rgba(10, 191, 173, 0.15);
  box-shadow: 0 0 20px rgba(10, 191, 173, 0.2);
}
.s1-dropzone__heading {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
  font-family: var(--font-display);
}
.s1-dropzone__sub {
  font-size: 0.84rem;
  color: var(--color-text-subtle);
  margin: 0;
}
.s1-dropzone__formats {
  display: flex;
  gap: 0.4rem;
  margin-top: 0.35rem;
}
.s1-dropzone__formats span {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 0.15rem 0.5rem;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: var(--color-text-ghost);
  font-family: var(--font-data);
  text-transform: uppercase;
}

/* File confirmed */
.s1-file-confirmed {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.s1-file-confirmed__row {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 1rem 1.1rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-elevated);
}
.s1-file-confirmed__row--done {
  border-color: rgba(0, 201, 122, 0.25);
  background: rgba(0, 201, 122, 0.04);
}
.s1-file-confirmed__icon {
  display: grid;
  place-items: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--color-border);
  color: var(--color-text-subtle);
  flex-shrink: 0;
}
.s1-file-confirmed__icon--done {
  background: rgba(0, 201, 122, 0.1);
  border-color: rgba(0, 201, 122, 0.3);
  color: var(--color-accent-2);
}
.s1-file-confirmed__meta {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  flex: 1;
  min-width: 0;
}
.s1-file-confirmed__meta strong {
  font-size: 0.9rem;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.s1-file-confirmed__meta span {
  font-size: 0.78rem;
  color: var(--color-text-subtle);
}
.s1-file-confirmed__change {
  background: none;
  border: 1px solid var(--color-border);
  color: var(--color-text-subtle);
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0.3rem 0.6rem;
  border-radius: var(--radius-sm);
  transition: color var(--transition-fast), border-color var(--transition-fast);
  flex-shrink: 0;
}
.s1-file-confirmed__change:hover {
  color: var(--color-accent);
  border-color: var(--color-accent);
}
.s1-upload-hint {
  font-size: 0.78rem;
  color: var(--color-text-subtle);
  margin: 0;
}

/* ── Tags ─────────────────────────────────────────────────────────────────── */
.s1-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.72rem;
  font-weight: 700;
  border-radius: var(--radius-full);
  padding: 0.18rem 0.5rem;
}
.s1-tag--success {
  background: rgba(0, 201, 122, 0.1);
  color: var(--color-accent-2);
  border: 1px solid rgba(0, 201, 122, 0.25);
}
.s1-tag--processing {
  background: rgba(10, 191, 173, 0.08);
  color: var(--color-accent);
  border: 1px solid rgba(10, 191, 173, 0.2);
}
.s1-tag__dot {
  width: 0.4rem;
  height: 0.4rem;
  border-radius: 50%;
  background: currentColor;
}
.s1-tag__spinner {
  display: inline-block;
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  border: 1.5px solid currentColor;
  border-top-color: transparent;
  animation: s1Spin 0.7s linear infinite;
}

/* ── Secondary panel ──────────────────────────────────────────────────────── */
.s1-upload-secondary {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  position: sticky;
  top: calc(3.5rem + 1.5rem);
}
.s1-preview-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-bg-elevated);
  padding: 1.25rem;
}
.s1-preview-card__title {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--color-text-subtle);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin: 0 0 1rem;
}
.s1-entity-preview {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.s1-entity-preview li {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}
.s1-entity-preview__icon {
  display: grid;
  place-items: center;
  width: 2rem;
  height: 2rem;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}
.s1-entity-preview__text strong {
  display: block;
  font-size: 0.84rem;
  color: var(--color-text);
  margin-bottom: 0.15rem;
}
.s1-entity-preview__text p {
  font-size: 0.76rem;
  color: var(--color-text-subtle);
  margin: 0;
  line-height: 1.5;
}
.s1-how-it-works {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-bg-elevated);
  padding: 1.1rem 1.25rem;
}
.s1-how-it-works__label {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--color-text-subtle);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin: 0 0 0.85rem;
}
.s1-hiw-steps {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.s1-hiw-steps li {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}
.s1-hiw-steps__num {
  display: grid;
  place-items: center;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  background: rgba(10, 191, 173, 0.1);
  border: 1px solid rgba(10, 191, 173, 0.25);
  color: var(--color-accent);
  font-size: 0.72rem;
  font-weight: 800;
  font-family: var(--font-display);
  flex-shrink: 0;
  margin-top: 0.1rem;
}
.s1-hiw-steps strong {
  display: block;
  font-size: 0.84rem;
  color: var(--color-text);
  margin-bottom: 0.15rem;
}
.s1-hiw-steps p {
  font-size: 0.76rem;
  color: var(--color-text-subtle);
  margin: 0;
  line-height: 1.5;
}

/* ── Building layout ──────────────────────────────────────────────────────── */
.s1-building-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 2rem;
  align-items: start;
}
.s1-building-primary {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.s1-building-file-row {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.75rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-elevated);
  font-size: 0.85rem;
}
.s1-building-file-row__icon {
  display: grid;
  place-items: center;
  width: 2rem;
  height: 2rem;
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--color-border);
  color: var(--color-text-subtle);
  flex-shrink: 0;
}
.s1-building-file-row__name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--color-text-muted);
  font-weight: 600;
}
.s1-progress-wrap {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}
.s1-progress-track {
  flex: 1;
  height: 5px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: var(--radius-full);
  overflow: hidden;
}
.s1-progress-fill {
  display: block;
  height: 100%;
  background: var(--gradient-accent);
  border-radius: var(--radius-full);
  transition: width 0.6s ease;
}
.s1-progress-pct {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--color-accent);
  font-family: var(--font-data);
  white-space: nowrap;
  min-width: 2.5rem;
  text-align: right;
}
.s1-extraction-log {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-base);
  padding: 1rem;
}
.s1-log-entry {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  font-size: 0.84rem;
  transition: opacity var(--transition-fast);
}
.s1-log-entry--pending { opacity: 0.3; }
.s1-log-entry--active { color: var(--color-text); }
.s1-log-entry--done { color: var(--color-text-muted); }
.s1-log-entry__icon {
  display: grid;
  place-items: center;
  width: 1.4rem;
  height: 1.4rem;
  border-radius: 50%;
  flex-shrink: 0;
}
.s1-log-entry--done .s1-log-entry__icon {
  background: rgba(0, 201, 122, 0.12);
  color: var(--color-accent-2);
}
.s1-log-entry--active .s1-log-entry__icon {
  background: rgba(10, 191, 173, 0.1);
  color: var(--color-accent);
}
.s1-log-spinner {
  display: block;
  width: 0.7rem;
  height: 0.7rem;
  border-radius: 50%;
  border: 1.5px solid var(--color-accent);
  border-top-color: transparent;
  animation: s1Spin 0.7s linear infinite;
}
.s1-log-dot {
  display: block;
  width: 0.35rem;
  height: 0.35rem;
  border-radius: 50%;
  background: var(--color-border-strong);
}
.s1-log-entry__text {
  flex: 1;
  min-width: 0;
}
.s1-log-entry__tag {
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--color-accent);
  background: rgba(10, 191, 173, 0.08);
  border: 1px solid rgba(10, 191, 173, 0.2);
  border-radius: var(--radius-full);
  padding: 0.1rem 0.4rem;
  white-space: nowrap;
}
.s1-building-secondary {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-bg-elevated);
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  position: sticky;
  top: calc(3.5rem + 1.5rem);
}
.s1-building-secondary__title {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--color-text-subtle);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin: 0;
}
.s1-scanning-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}
.s1-scanning-item {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.5rem 0.65rem;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  transition: border-color var(--transition-fast), background var(--transition-fast);
}
.s1-scanning-item--found {
  border-color: rgba(0, 201, 122, 0.2);
  background: rgba(0, 201, 122, 0.04);
}
.s1-scanning-item__icon {
  display: grid;
  place-items: center;
  width: 1.75rem;
  height: 1.75rem;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}
.s1-scanning-item__text {
  flex: 1;
  min-width: 0;
}
.s1-scanning-item__text strong {
  display: block;
  font-size: 0.8rem;
  color: var(--color-text-muted);
}
.s1-scanning-item__found { font-size: 0.7rem; font-weight: 700; color: var(--color-accent-2); }
.s1-scanning-item__scanning { font-size: 0.7rem; color: var(--color-accent); animation: s1Blink 1.2s ease-in-out infinite; }
.s1-scanning-item__waiting { font-size: 0.7rem; color: var(--color-text-ghost); }
.s1-scanning-item__check { flex-shrink: 0; }
.s1-building-secondary__footnote {
  display: flex;
  align-items: flex-start;
  gap: 0.4rem;
  font-size: 0.72rem;
  color: var(--color-text-ghost);
  line-height: 1.5;
  padding-top: 0.5rem;
  border-top: 1px solid var(--color-border);
}

/* ── Ready: stat row ──────────────────────────────────────────────────────── */
.s1-stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.85rem;
}
.s1-stat-card {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 1rem 1.25rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-elevated);
}
.s1-stat-card--accent {
  border-color: rgba(0, 201, 122, 0.25);
  background: rgba(0, 201, 122, 0.04);
}
.s1-stat-card strong {
  font-size: 1.75rem;
  font-family: var(--font-display);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--color-text);
  line-height: 1;
}
.s1-stat-card--accent strong { color: var(--color-accent-2); }
.s1-stat-card span {
  font-size: 0.76rem;
  color: var(--color-text-subtle);
  font-weight: 600;
}

/* ── Ready: success banner ────────────────────────────────────────────────── */
.s1-success-banner {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 0.85rem 1.1rem;
  border: 1px solid rgba(0, 201, 122, 0.3);
  border-radius: var(--radius-md);
  background: rgba(0, 201, 122, 0.06);
  flex-wrap: wrap;
}
.s1-success-banner__pulse {
  flex-shrink: 0;
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 50%;
  background: var(--color-accent-2);
  box-shadow: 0 0 8px rgba(0, 201, 122, 0.5);
  animation: s1Pulse 2s ease-in-out infinite;
}
.s1-success-banner__text {
  flex: 1;
  font-size: 0.875rem;
  color: var(--color-text-muted);
  margin: 0;
  min-width: 200px;
}
.s1-success-banner__text strong { color: var(--color-text); }

/* ── Ready: full-width graph with floating overlay ──────────────────────────── */
.s1-graph-wrap {
  position: relative;
}
.s1-graph-panel {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-bg-elevated);
  overflow: hidden;
}
.s1-graph-panel__canvas { min-height: 520px; }

/* Floating entities toggle button */
.s1-entities-toggle {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  z-index: 20;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.8rem 0.4rem 0.65rem;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 0.18s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  white-space: nowrap;
}
.s1-entities-toggle:hover,
.s1-entities-toggle--active {
  background: rgba(10, 191, 173, 0.08);
  border-color: rgba(10, 191, 173, 0.35);
  color: var(--color-accent);
}
.s1-entities-toggle__count {
  font-size: 0.68rem;
  font-weight: 700;
  font-family: var(--font-data, monospace);
  background: rgba(10, 191, 173, 0.12);
  color: var(--color-accent);
  padding: 0.05rem 0.4rem;
  border-radius: var(--radius-full);
}
.s1-entities-toggle__chevron {
  transition: transform 0.2s ease;
}
.s1-entities-toggle__chevron.flipped {
  transform: rotate(180deg);
}

/* Floating breakdown overlay panel */
.s1-breakdown-panel {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 280px;
  z-index: 15;
  border-left: 1px solid var(--color-border);
  border-radius: 0 var(--radius-lg) var(--radius-lg) 0;
  background: var(--color-bg-elevated);
  backdrop-filter: blur(12px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: -8px 0 32px rgba(0, 0, 0, 0.18);
}

/* Transition */
.s1-drawer-enter-active,
.s1-drawer-leave-active { transition: transform 0.22s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.18s ease; }
.s1-drawer-enter-from,
.s1-drawer-leave-to { transform: translateX(100%); opacity: 0; }

.s1-breakdown-panel__head {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.9rem 1rem;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}
.s1-breakdown-close {
  margin-left: auto;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  width: 1.6rem;
  height: 1.6rem;
  border-radius: var(--radius-sm);
  background: transparent;
  border: 1px solid transparent;
  cursor: pointer;
  color: var(--color-text-ghost);
  transition: all 0.15s ease;
}
.s1-breakdown-close:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: var(--color-border);
  color: var(--color-text-muted);
}
.s1-breakdown-panel__title {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  margin: 0 0 0.15rem;
  padding: 0;
}
.s1-breakdown-panel__sub {
  font-size: 0.7rem;
  color: var(--color-text-subtle);
  margin: 0;
  padding: 0;
}
.s1-breakdown-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem 0;
}
.s1-breakdown-section {
  padding: 0 1rem;
  margin-bottom: 0.5rem;
}
.s1-breakdown-section__head {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.45rem;
}
.s1-breakdown-section__icon {
  display: grid;
  place-items: center;
  width: 1.65rem;
  height: 1.65rem;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}
.s1-breakdown-section__label {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  flex: 1;
  min-width: 0;
}
.s1-breakdown-section__count {
  font-size: 0.72rem;
  font-weight: 700;
  font-family: var(--font-data);
  color: var(--color-text-ghost);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  padding: 0.1rem 0.4rem;
}
.s1-breakdown-section__nodes {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
.s1-breakdown-node {
  font-size: 0.82rem;
  color: var(--color-text-subtle);
  padding: 0.3rem 0.5rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast);
  border: 1px solid transparent;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.s1-breakdown-node:hover {
  background: rgba(255, 255, 255, 0.04);
  color: var(--color-text-muted);
}
.s1-breakdown-node--selected {
  background: rgba(10, 191, 173, 0.08);
  color: var(--color-accent);
  border-color: rgba(10, 191, 173, 0.2);
}
.s1-breakdown-panel__footer {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.7rem 1rem;
  border-top: 1px solid var(--color-border);
  font-size: 0.74rem;
  color: var(--color-text-ghost);
  background: var(--color-bg-base);
}
.s1-breakdown-panel__footer span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

/* ── Node drawer ──────────────────────────────────────────────────────────── */
.s1-node-type-chip { margin-bottom: 1rem; }
.s1-node-type-chip span {
  display: inline-block;
  font-size: 0.74rem;
  font-weight: 700;
  border-radius: var(--radius-full);
  padding: 0.2rem 0.65rem;
}
.s1-node-dl { display: grid; gap: 0.75rem; }
.s1-node-dl dt {
  font-size: 0.72rem;
  color: var(--color-text-subtle);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-weight: 700;
}
.s1-node-dl dd {
  margin: 0.2rem 0 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-muted);
}
.s1-node-empty {
  font-size: 0.84rem;
  color: var(--color-text-subtle);
}

/* ── Animations ───────────────────────────────────────────────────────────── */
@keyframes s1Spin { to { transform: rotate(360deg); } }
@keyframes s1Pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 8px rgba(0, 201, 122, 0.5); }
  50% { opacity: 0.6; box-shadow: 0 0 16px rgba(0, 201, 122, 0.8); }
}
@keyframes s1Blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ── Responsive ───────────────────────────────────────────────────────────── */
@media (max-width: 1100px) {
  .s1-guided-layout {
    grid-template-columns: 1fr 280px;
  }
}
@media (max-width: 960px) {
  .s1-entry-cards {
    grid-template-columns: 1fr;
    max-width: 480px;
  }
  .s1-guided-layout,
  .s1-upload-layout,
  .s1-building-layout {
    grid-template-columns: 1fr;
  }
  .s1-guided-secondary,
  .s1-upload-secondary,
  .s1-building-secondary {
    position: static;
  }
  .s1-stat-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .s1-ready-layout {
    grid-template-columns: 1fr;
  }
  .s1-breakdown-panel {
    position: static;
    max-height: none;
  }
  .s1-objective-grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 600px) {
  .s1-form-grid {
    grid-template-columns: 1fr;
  }
  .s1-product-row__fields {
    grid-template-columns: 1fr;
  }
  .s1-stat-row {
    grid-template-columns: 1fr 1fr;
  }
  .s1-dropzone {
    padding: 2.5rem 1.25rem;
  }
  .s1-stepper {
    gap: 0.25rem;
  }
}
</style>
