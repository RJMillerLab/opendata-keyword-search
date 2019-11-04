(ns search-opendata.core
  (:require-macros [cljs.core.async.macros :refer [go]])
  (:require [reagent.core :as r]
            [cljs.core.async :refer [<!]]
            [cljs-http.client :as http]
            [clojure.string :as string]
            [clojure.pprint :refer [pprint]]))

(defn lower [x]
  (cond (nil? x) "***NIL***"
        (string? x) (string/lower-case x)
        :else (str x)))

(def state (r/atom {:query-string ""
                    :query-expand false
                    :search-data false
                    :phase nil}))

(defn update-query-string!
  [val]
  (swap! state assoc :query-string val))

(defn toggle!  [k] (swap! state update k not))

(defn start-query!
  [offset limit]
  (let [{:keys [query-string 
                query-expand
                search-data]} @state]
    (swap! state assoc :results nil :phase :inprogress)
    (go (let [params {"q" query-string
                      "expand" (if query-expand "1" "")
                      "offset" offset
                      "limit" limit
                      "prefix" (if search-data "D" "S")}
              r (<! (http/get "http://rtr.science.uoit.ca:8998/search"
                              {:with-credentials? false
                               :query-params params}))]
          (if (:success r)
            (swap! state 
                   assoc 
                   :results (:body r)
                   :phase :complete))))))


(declare Header)
(declare SearchForm)
(declare SearchResults)
(declare SummarizeResults)
(declare RenderEntry)
(declare Paginate)


(defn Home []
  [:div.container
   [Header]
   [SearchForm]
   [SummarizeResults (:results @state)]
   (if-let [results (:results @state)]
     [:div
      [Paginate results]
      [SearchResults results]])
   ]
  )

(defn Header []
  [:div.jumbotron
   [:h1 "Search in Open Data"]
   [:p "Providing keyword search over open data lakes"]])

(defn SearchForm []
  [:form.form-horizontal 
   {:on-submit (fn [e] (do (.preventDefault e) (start-query! 0 10)))}
   [:div.form-group
    [:label.col-sm-2.control-label "Query"]
    [:div.col-sm-8
      [:input.form-control {:type "text" 
                            :placeholder "Your keywords here"
                            :on-change #(-> % .-target .-value update-query-string!)}]]]
   [:div.form-group
    [:div.col-sm-offset-2.col-sm-8
     [:div.checkbox
      [:label 
       [:input {:type "checkbox"
                :checked (:query-expand @state)
                :on-change #(do (toggle! :query-expand)
                                (start-query! 0 10))}]
       "Semantic Similarity"]
      [:label
       {:style {:margin-left 30}}
       [:input {:type "checkbox"
                :checked (:search-data @state)
                :on-change #(do (toggle! :search-data)
                                (start-query! 0 10))}]
       "Search in data"]
      [:button.btn.btn-default 
       {:style {:float :right}
        :type :submit} "Run"]]]]
   ])

(defn SearchResults [results]
  (let [terms (mapv lower (:query results))]
    [:div.search-results
     [:ul.list-group
      (for [entry (:entries results)]
        [:li.list-group-item
         {:key (:docid entry)}
         [:span.badge (str (:percent entry) "%")]
         [RenderEntry entry terms]])]]))

(defn SummarizeResults [results]
  (case (:phase @state)
    :inprogress [:div.summarize-result [:p "In progress..."]]
    :complete
    [:div.summarize-results
     [:p "The query terms are: "
      (for [[i term] (map-indexed vector (:query results))
            :let [first? (zero? i)
                  last? (= i (dec (count (:query results))))]]
        (cond
          (and first? last?) [:span {:key i} [:em term] "."]
          last?  [:span {:key i} " and " [:em term] "."]
          :else  [:span {:key i} [:em term] ", "]))]
     [:p 
      "Out of " (:total results)
      ", these are the results from "
      [:b (inc (:offset results)) " to " (inc (+ (:offset results) (:limit results)))]]]
    nil))

(defn Paginate [results]
  (let [{:keys [total offset limit]
         :or {total 0
              offset 0
              limit 10}} results
        num-pages (.ceil js/Math (/ total limit))]
    [:nav {:style {:display :flex
                   :justify-content :center}}
     [:ul.pagination
      (for [i (range (min 10 num-pages))
            :let [next-offset (* i limit)
                  current? (= i (.floor js/Math (/ offset limit)))]]
        [:li {:key i
              :class (if current? "active")
              :on-click (fn [e]
                          (do (.preventDefault e)
                              (.stopPropagation e)
                              (start-query! next-offset limit)))}
         [:a {:href "#"} (str (inc i))]])]]))

(defn scalar? [x]
  (or (string? x) (number? x) (nil? x)))

(defn flat
  "flattens the entry for a specific key"
  [data & [path]]
  (let [path (or path [])]
    (loop [result []
           ks (if (vector? data)
                (range (count data))
                (keys data))]
      (if (empty? ks)
        result
        (let [k (first ks)
              v (get data k)
              new-path (conj path k)]
          (cond 
            (vector? v) (recur (into result (flat v new-path)) (rest ks))
            (map? v) (recur (into result (flat v new-path)) (rest ks))
            :else (recur (conj result [new-path (str v)]) (rest ks))))))))

(defn includes? [text terms]
  (some #(string/includes? (lower text) %) terms))

(defn find-term [text term from-index]
  (when-not (empty? term)
    (if-let [index (string/index-of text term from-index)]
      {:start index 
       :end (+ index (count term))
       :term term})))

(defn term-matches [text terms]
  (loop [sections []
         from-index 0]
    (if-let [match (some #(find-term text % from-index) terms)]
      (let [new-sections (if (< from-index (:start match))
                           (into sections [{:start from-index
                                            :end (:start match)}
                                           match])
                           (conj sections match))]
        (recur new-sections (:end match)))
      (conj sections {:start from-index :end (count text)}))))

(defn Highlight [value terms]
  (let [value (str value)
        text (lower value)
        sections (term-matches text terms)]
    [:div
     (for [[i section] (map-indexed vector sections)
           :let [text (subs value (:start section) (:end section))
                 term (:term section)
                 cls (if term "highlight" "")]]
       [:span {:key i :class cls} text])]))

(declare RenderEntrySchema 
         RenderEntryData)

(defn RenderEntry
  [entry terms]
  (let [schema (js->clj (.parse js/JSON (:schema entry)))]
    [:div.render-entry
     [:div 
      [:span {:style {:font-weight :bold}} (inc (:rank entry))] 
      [:a {:href "#"
           :style {:margin-left 10}} (:dataset_id entry)]
      [Highlight (get-in schema ["resource" "description"]) terms]]
     (case (:search_prefix entry)
       "S" [RenderEntrySchema schema terms]
       "D" [RenderEntryData entry terms])]))

(defn RenderEntrySchema
  [schema terms]
  [:table.render-entry
   [:tbody
     (for [[i [path value]] (map-indexed vector (flat schema))
           :let [path-string (string/join "/" (map str path))]
           :when (includes? value terms)
           ]
       [:tr {:key i}
        [:td path-string]
        [:td [Highlight value terms]]])]])

(defn parse-table-data [table-string]
  (for [line (string/split table-string "\n\n")]
    line))

(defn RenderEntryData
  [entry terms]
  (let [rows (js->clj (.parse js/JSON (:table entry)))
        columns (sort (map first (first rows)))]
    [:table.render-entry
     [:tbody
      [:tr (for [k columns]
             [:td {:key k
                   :style {:font-weight :bold}} k])]
      (for [[i row] (map-indexed vector rows)]
        [:tr {:key i} 
         (for [k columns]
           [:td {:key (str k i)} 
            [Highlight (get row k "") terms]])])]]))

;; -------------------------
;; Initialize app

(defn mount-root []
  (r/render [Home] (.getElementById js/document "app")))

(defn init! []
  (mount-root))
