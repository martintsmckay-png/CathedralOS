// CathedralOS — Doctrine Navigator (Level 9)
import { DoctrineIndex } from "./doctrine-index.js";
import { EventStream } from "./eventStream.js";

export const DoctrineNavigator = (() => {
  let activeQuery = "";
  let selectedCategory = "All";

  function setFilter(category, keyword = "") {
    selectedCategory = category;
    activeQuery = keyword.toLowerCase();

    EventStream.emit({
      type: "NAVIGATOR_FILTER_CHANGED",
      subsystem: "DoctrineNavigator",
      detail: { category, keyword }
    });
  }

  function query() {
    const fullIndex = DoctrineIndex.index();
    let results = [];

    // Flatten or filter by primary category
    if (selectedCategory === "All") {
      Object.keys(fullIndex).forEach(cat => {
        results = results.concat(fullIndex[cat]);
      });
    } else if (fullIndex[selectedCategory]) {
      results = [...fullIndex[selectedCategory]];
    }

    // Apply text matching search query
    if (activeQuery) {
      results = results.filter(entry => 
        entry.text.toLowerCase().includes(activeQuery) || 
        entry.id.toLowerCase().includes(activeQuery)
      );
    }

    return results;
  }

  return { setFilter, query };
})();

