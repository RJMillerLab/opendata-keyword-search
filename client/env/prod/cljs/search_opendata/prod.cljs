(ns search-opendata.prod
  (:require
    [search-opendata.core :as core]))

;;ignore println statements in prod
(set! *print-fn* (fn [& _]))

(core/init!)
